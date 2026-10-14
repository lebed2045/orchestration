import importlib.machinery
import importlib.util
import io
import pathlib
import unittest
from unittest import mock


PATH = pathlib.Path(__file__).with_name("agy-peer-mcp")
loader = importlib.machinery.SourceFileLoader("agy_peer_mcp", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
bridge = importlib.util.module_from_spec(spec)
loader.exec_module(bridge)


class AgyPeerMcpTests(unittest.TestCase):
    def test_primary_route_wins(self):
        with mock.patch.object(bridge, "_run_agy", return_value=(True, "review")):
            with mock.patch.object(bridge, "_run_proxy") as fallback:
                result = bridge.ask("inspect", 10)
        self.assertIn("[route: agy", result)
        self.assertIn("review", result)
        fallback.assert_not_called()

    def test_failed_primary_uses_proxy(self):
        with mock.patch.object(bridge, "_run_agy", return_value=(False, "quota")):
            with mock.patch.object(bridge, "_run_proxy", return_value="fallback") as fallback:
                result = bridge.ask("inspect", 10)
        self.assertEqual(result, "fallback")
        fallback_prompt = fallback.call_args.args[0]
        self.assertIn("independent read-only reviewer", fallback_prompt)
        self.assertTrue(fallback_prompt.endswith("inspect"))

    def test_expected_mcp_tools_are_exposed(self):
        response = bridge._response({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(names, {"agy_ask", "agy_continue", "agy_status"})

    def test_total_route_failure_is_json_rpc_error(self):
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "agy_ask", "arguments": {"prompt": "review"}},
        }
        with mock.patch.object(bridge, "_run_agy", return_value=(False, "quota")):
            with mock.patch.object(
                bridge,
                "_run_proxy",
                side_effect=bridge.GeminiUnavailableError("proxy offline"),
            ):
                response = bridge._response(request)
        self.assertEqual(response["id"], 7)
        self.assertEqual(response["error"]["code"], -32000)
        self.assertIn("GEMINI_UNAVAILABLE", response["error"]["message"])
        self.assertNotIn("result", response)

    def test_cli_uses_the_same_router(self):
        with mock.patch.object(bridge, "ask", return_value="routed") as ask:
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                result = bridge._cli(["ask", "review", "this"])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "routed\n")
        ask.assert_called_once_with("review this", bridge.DEFAULT_TIMEOUT, continuation=False)

    def test_cli_status_does_not_generate(self):
        with mock.patch.object(bridge, "status", return_value="ready") as status:
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                result = bridge._cli(["status"])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "ready\n")
        status.assert_called_once_with()


CATALOG = """Fetching available models...
gemini-3.8-flash-high	Gemini 3.8 Flash (High)
gemini-3.8-flash-medium	Gemini 3.8 Flash (Medium)
gemini-3.7-flash-high	Gemini 3.7 Flash (High)
gemini-3.1-pro-high	Gemini 3.1 Pro (High)
claude-opus-4-6-thinking	Claude Opus 4.6 (Thinking)
"""


class ModelResolutionTests(unittest.TestCase):
    def setUp(self):
        bridge._MODEL_CACHE.clear()

    def tearDown(self):
        bridge._MODEL_CACHE.clear()

    def _catalog(self, stdout=CATALOG, returncode=0):
        return mock.patch.object(
            bridge.subprocess,
            "run",
            return_value=mock.Mock(returncode=returncode, stdout=stdout, stderr=""),
        )

    def test_resolves_highest_flash_high_from_live_catalog(self):
        with mock.patch.object(bridge.shutil, "which", return_value="/usr/bin/agy"):
            with self._catalog():
                self.assertEqual(bridge.resolve_model(), "Gemini 3.8 Flash (High)")

    def test_no_retired_model_literal_is_frozen_in_source(self):
        source = PATH.read_text()
        self.assertNotIn("Gemini 3.5 Flash", source)

    def test_run_agy_passes_the_resolved_model(self):
        with mock.patch.object(bridge, "resolve_model", return_value="Gemini 9 Flash (High)"):
            with mock.patch.object(bridge.shutil, "which", return_value="/usr/bin/agy"):
                with mock.patch.object(
                    bridge.subprocess,
                    "run",
                    return_value=mock.Mock(returncode=0, stdout="ok", stderr=""),
                ) as run:
                    ok, _ = bridge._run_agy("p", 10)
        self.assertTrue(ok)
        self.assertIn("Gemini 9 Flash (High)", run.call_args.args[0])

    def test_status_is_ok_when_resolver_finds_a_model(self):
        with mock.patch.object(bridge, "resolve_model", return_value="Gemini 3.8 Flash (High)"):
            with mock.patch.object(bridge, "_proxy_json", side_effect=OSError("down")):
                report = bridge.status()
        self.assertIn("primary agy: ok", report)

    def test_unresolvable_catalog_reports_failure_not_a_guess(self):
        with mock.patch.object(bridge.shutil, "which", return_value="/usr/bin/agy"):
            with self._catalog(stdout="Fetching available models...\n", returncode=0):
                self.assertIsNone(bridge.resolve_model())


if __name__ == "__main__":
    unittest.main()
