# /think — Council of Opus + Codex + Antigravity. One-shot, peer-reviewed, anti-sycophancy.

**THINK_VERSION:** `v1` · **THINK_COMMITTED:** `08-jun-2026` · **Tag:** `[council-default | peer-review | anti-syco | persona-card]`

**First line of every run must be, verbatim:** `think v1 (08-jun-2026)` — derived from the two values above. Bump both when the deliberation logic changes meaningfully.

A third primitive next to `/wf` (do) and `/r` (find): for open / introspective / "what do you think?" questions where there is no objective ground truth. Implements **Karpathy's LLM Council** (parallel → anonymized peer review → chair synthesis) with **forced reasoning-method diversity** (ngmeyer/council-review). Anti-sycophancy is load-bearing, not decorative.

## Usage

```bash
/think <topic>                       # default: 3-agent council (Opus + Codex + Antigravity)
/think --solo <topic>                # Opus only — fast, no peer review
/think --nudge "<pushback>"          # re-deliberate on most-recent think-*.md with new context
/think --vault <path> <topic>        # OPT-IN journal RAG — DEFERRED to v2, ignored in v1
```

**Default behavior:** all three EIs in parallel. The `-cg` is not an opt-in here — it is the point of the command. Flags subtract.

---

## When to Use /think vs /r vs /wf

| Command | When | Output |
|---|---|---|
| `/wf` | "Build/fix/refactor this code." Ground truth: tests pass. | Code diff + EXECUTION_BLOCK |
| `/r` | "Tell me how X is done. Stand on giants." Ground truth: cited sources. | Research doc in `.claude/research/` |
| `/think` | "What do you think? What do I do? Am I right that…?" No ground truth. | Council synthesis + dissent + framing critique |

If the question has tests, it's `/wf`. If the question has citations, it's `/r`. If the question is about *you*, it's `/think`. (This table tells the USER which command fits — never auto-route into `/wf`; it runs only on explicit invocation.)

---

## Flag Detection

```bash
SOLO=false
NUDGE=""
VAULT_PATH=""
TOPIC="$ARGUMENTS"

# --solo
if [[ "$TOPIC" == *"--solo"* ]]; then
  SOLO=true
  TOPIC="${TOPIC//--solo/}"
fi

# --nudge "..."
if [[ "$TOPIC" == *"--nudge"* ]]; then
  NUDGE=$(echo "$TOPIC" | sed -n 's/.*--nudge[[:space:]]*"\([^"]*\)".*/\1/p')
  [ -z "$NUDGE" ] && NUDGE=$(echo "$TOPIC" | sed -n 's/.*--nudge=\([^ ]*\).*/\1/p')
  TOPIC="${TOPIC//--nudge \"$NUDGE\"/}"
  TOPIC="${TOPIC//--nudge=$NUDGE/}"
fi

# --vault <path> (deferred to v2)
if [[ "$TOPIC" == *"--vault"* ]]; then
  VAULT_PATH=$(echo "$TOPIC" | sed -n 's/.*--vault[[:space:]]\+\([^ ]*\).*/\1/p')
  TOPIC="${TOPIC//--vault $VAULT_PATH/}"
  echo "[INFO] --vault is documented but NOT implemented in v1. Ignoring '$VAULT_PATH'. Persona card only."
fi

TOPIC="${TOPIC## }"; TOPIC="${TOPIC%% }"

# Slug from topic (mirrors r.md convention)
SLUG=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | cut -c 1-60)
[ -z "$SLUG" ] && SLUG="think-$(date +%s)"
OUTPUT=".claude/research/think-${SLUG}.md"

echo "TOPIC: $TOPIC"
echo "SOLO: $SOLO"
echo "OUTPUT: $OUTPUT"
[ -n "$NUDGE" ] && echo "NUDGE: $NUDGE"

# Timing ledger (always-on). Total wall time is computed from this file at completion; never estimated.
T_RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)                  # UTC stamp; lexical sort == chronological
T_LEDGER=".claude/temp/think/$T_RUN_ID/started.txt"
mkdir -p ".claude/temp/think/$T_RUN_ID"
{ date +%s; date '+%Y-%m-%d %H:%M:%S'; } > "$T_LEDGER"   # line 1 = epoch, line 2 = human start
echo "timing ledger: $T_LEDGER"
```

---

## Phase 0: PREFLIGHT

**Cheap probes only.** No live MCP pings — namespace presence is enough. ("Save those MCP calls and work.")

### 0a. Codex MCP availability

Run:
```
ToolSearch({query: "select:mcp__codex-cli__codex,mcp__codex-cli__codex-reply", max_results: 2})
```

If both schemas come back, `CODEX_AVAILABLE=true`. If only one or none, `CODEX_AVAILABLE=false` and capture the reason for the user-visible degradation line.

**HARD RULE (quoted from `wf.md:316`):** *"Model + reasoning effort inherit from `~/.codex/config.toml` — do not pass `model` or reasoning override unless you need to deviate."* For `/think` we never deviate. Currently `~/.codex/config.toml` resolves to `model = "gpt-5.5"`, `model_reasoning_effort = "xhigh"` — but the command must work for any future value without edits. **Never type a model name into a `mcp__codex-cli__codex` call from this command.**

### 0b. Antigravity (agy bridge MCP) availability

```text
# Bridge tool presence check — the agy bridge MCP exposes agy_ask/agy_continue/agy_status
ToolSearch({query: "select:mcp__agy__agy_ask,mcp__agy__agy_continue,mcp__agy__agy_status", max_results: 3})
# AGY_AVAILABLE=true iff mcp__agy__agy_ask is loaded
```

The bridge wraps `agy` (config under `~/.gemini/`) and reads its transcript files. Model is fixed to Gemini 3.5 Flash (High) by the bridge — the command never passes a model. Register once: `claude mcp add agy -- ~/.claude/mcp-servers/agy-bridge/.venv/bin/python ~/.claude/mcp-servers/agy-bridge/server.py`, then restart Claude Code.

The bridge owns quota handling. It detects 429 `RESOURCE_EXHAUSTED` from `agy` stdout/stderr and `~/.gemini/antigravity-cli/log/cli-*.log`; if free Gemini quota is exhausted, it automatically routes the same prompt to Vertex `gemini-3.5-flash` on project `gemini-keroga-260526-3895`, location `global`, using service account key `~/dev_local/temp/google300/vertex-key.json` unless overridden by environment. A response prefixed `[agy quota exhausted — auto-routed to Vertex gemini-3.5-flash on project gemini-keroga-260526-3895]` is a valid Gemini council response, not a downgrade. Do not substitute Codex/self-deliberation because Vertex credits would be used; Vertex is the intended Gemini fallback. If the bridge was updated but still behaves like the old agy-only bridge, restart Claude Code so the MCP server reloads.

### 0c. USER.md persona card

```bash
USER_CARD="$HOME/.claude/USER.md"
if [ ! -f "$USER_CARD" ]; then
  echo "STOP: ~/.claude/USER.md not found."
  # Orchestrator writes the template (see "USER.md Template" section near the end).
  echo "Created template at $USER_CARD."
  echo "Open it, fill in the sections (2-5 min), then re-run /think."
  exit 1
fi
```

The template is in the **USER.md Template** section at the end of this file. The orchestrator writes it verbatim with the `Write` tool, then halts.

### 0d. Council size + degradation surface

```bash
if [ "$SOLO" = "true" ]; then
  CODEX_AVAILABLE=false
  AGY_AVAILABLE=false
fi

COUNCIL_SIZE=1
[ "$CODEX_AVAILABLE" = "true" ] && COUNCIL_SIZE=$((COUNCIL_SIZE + 1))
[ "$AGY_AVAILABLE"   = "true" ] && COUNCIL_SIZE=$((COUNCIL_SIZE + 1))

DEGRADE_NOTE=""
if [ "$SOLO" != "true" ] && [ "$COUNCIL_SIZE" = "1" ]; then
  DEGRADE_NOTE="Both external EIs unavailable. Running auto-solo (Opus only)."
elif [ "$SOLO" != "true" ] && [ "$CODEX_AVAILABLE" = "false" ]; then
  DEGRADE_NOTE="Council ran with 2 agents (Codex unavailable)."
elif [ "$SOLO" != "true" ] && [ "$AGY_AVAILABLE" = "false" ]; then
  DEGRADE_NOTE="Council ran with 2 agents (Antigravity unavailable: agy bridge MCP not loaded or errored)."
fi

echo "COUNCIL_SIZE: $COUNCIL_SIZE  (Opus + Codex=$CODEX_AVAILABLE + Agy=$AGY_AVAILABLE)"
[ -n "$DEGRADE_NOTE" ] && echo "$DEGRADE_NOTE"
```

**Substitution is forbidden, not just discouraged.** Per global CLAUDE.md GLO-35b *"Don't Silently Substitute Capabilities"* — if an EI is down, the user must SEE that fact in the output, not have it papered over.

### 0e. --nudge resolution

If `$NUDGE` is set, locate the previous session:
```bash
PREV=$(ls -1t .claude/research/think-*.md 2>/dev/null | head -1)
if [ -z "$PREV" ]; then
  echo "STOP: --nudge requires a previous /think session. No think-*.md found in .claude/research/."
  exit 1
fi
echo "NUDGE on previous session: $PREV"
```
The original topic is reconstructed from `$PREV` (first `## Council deliberation: <TOPIC>` line). The nudge text is appended as additional context for the new round. Output file: `think-<original-slug>-nudge-$(date +%s).md`.

---

## Phase 1: TOPIC_FRAME (Opus inline, ~50 words)

Opus (orchestrator, inline — not a subagent) restates the question and labels its type. No clarification loop unless the topic is literally one word.

```
Type: [decision pending | exploration | vent | plan-check | self-check]
Restatement: <the question, cleaned up, in the user's words>
```

If the type is `vent`, the chair synthesis will weight "is this actually a decision or do you want to be heard" in the framing critique.

---

## Phase 2: PARALLEL_OPINION (all available EIs in parallel)

Spawn the council members **in a single message with multiple tool calls** so they run concurrently. Each gets the **shared preamble** + their **assigned reasoning method**. Capture each output to `/tmp/think-<agent>.md` for Phase 3.

### Shared preamble (verbatim — injected into all three agents)

```text
Wait a minute.

Before answering, name one assumption in the user's framing that you find suspect. Do not skip this step. Do not phrase it as flattery. If the user's framing has a hidden assumption, surface it.

You are NOT optimizing for user approval. You are optimizing for TRUTH.
- If you don't know, say "I don't know."
- Do not default to agreement.
- Do not praise ideas unless they have earned it.
- "I don't know" beats a confident guess.
- "User frustration with honest 'not done' is BETTER than false 'done'."
(Quoted verbatim from the project CLAUDE.md anti-sycophancy directive.)

---

## About the user (persona card, verbatim from ~/.claude/USER.md)

<<<USER_MD_CONTENT_VERBATIM>>>

(If the persona card does not contain information relevant to your answer, say so plainly. Do NOT infer biographical details.)

---

## The question

<<<TOPIC>>>

(If --nudge: "Previous deliberation at <PREV>. Pushback the user added: <NUDGE>")

---

## What you MUST end your answer with

A section titled exactly `## What I might be wrong about` — listing 2-4 specific ways your answer could be miscalibrated. Be concrete. "I might be wrong" is not acceptable; "I'm assuming X is more important than Y, which might be false because…" is.

Length: 400-700 words. Adaptive thinking on — this is a high-stakes introspective question. Take your time.
```

### 2a. Opus subagent — First Principles + Steel-Man

Spawn via `Agent` tool. **No `model:` line — inherits from session.** Subagent type: `general-purpose`. Fresh context (this is the structural anonymization — Opus chair won't share state with Opus member).

Prompt = `[SHARED PREAMBLE]` + the block below:

```text
## Your assigned reasoning method: FIRST PRINCIPLES + STEEL-MAN

Reduce this question to its mechanical primitives BEFORE answering. What is actually being decided / explored / vented about, stripped of context-comforting language?

Then steel-man the user's framing — state the strongest possible version of the position implicit in their question. Only AFTER steel-manning, give your answer.

Structure your response with these headers, in this order:
## Mechanical primitives
## Steel-man of the user's framing
## My answer
## What I might be wrong about
```

Capture to `/tmp/think-opus.md`.

### 2b. Codex MCP — Contrarian / Inversion

**No `model`. No `reasoningEffort`. Both inherit from `~/.codex/config.toml`.**

```
mcp__codex-cli__codex({
  prompt: <[SHARED PREAMBLE] + the block below>
  // Do NOT add any other parameters. The Codex CLI picks model + reasoning from its own config.
})
```

Prompt body:

```text
## Your assigned reasoning method: CONTRARIAN / INVERSION

Assume the user's current direction (whatever they're contemplating, deciding, leaning toward) FAILS in 6 months. Trace backward to why. Be specific. What's the most likely failure mode? What signal would they see first if the failure path were real?

Only AFTER the inversion — give your answer.

Structure your response with these headers, in this order:
## If this fails, here's how
## Earliest detectable signal
## My answer (given the inversion)
## What I might be wrong about
```

Capture the tool response to `/tmp/think-codex.md`.

### 2c. Antigravity (agy bridge MCP) — Expansionist / Analogy

Call the `mcp__agy__agy_ask` MCP tool (Gemini 3.5 Flash via the agy bridge) with `timeout_s=120`. It returns the model's final text directly — save it to `/tmp/think-agy.md`. The bridge reads agy's transcript files, so the old headless-stdout hang is gone; no background PID/kill management needed.

```text
mcp__agy__agy_ask  timeout_s=120  prompt="
[SHARED PREAMBLE — with USER.md content + TOPIC interpolated before this prompt]

## Your assigned reasoning method: EXPANSIONIST / ANALOGY

Find the closest analogous situation in a DIFFERENT domain — not the user's domain, not the obvious adjacent one. (Career question → look at evolutionary biology, chess endgames. Relationship question → institutional design, supply-chain dependencies. Creative block → sleep research, jazz improvisation.) What did people in that domain learn the hard way?

Then map the analogy back to the user's question — but ONLY where the mapping survives mechanical scrutiny. Drop the parts that don't transfer.

Structure your response with these headers, in this order:
## Analogous situation (different domain)
## What survives the mapping
## What does NOT survive
## My answer (via the surviving analogy)
## What I might be wrong about
"
```

The `mcp__agy__agy_ask` call is synchronous and bounded by `timeout_s`. If it errors or exceeds the timeout, treat agy as unavailable: `AGY_AVAILABLE=false; COUNCIL_SIZE=$((COUNCIL_SIZE - 1))` and continue with the remaining council members.

If the response is truncated and `mcp__agy__agy_continue` is available, continue the same council-member conversation before marking the Antigravity pass failed.

---

## Phase 3: PEER_REVIEW (skip if COUNCIL_SIZE < 2)

Opus (inline) reads the available responses in **anonymized order**. The orchestrator shuffles letter assignments per session (`A`, `B`, `C`) and keeps the mapping in a local variable for de-anonymization in Phase 4.

Prompt to Opus (inline):

```text
You are the chair of an LLM council. You will now anonymously review the responses below.

CRITICAL: Do not write any text other than the FINAL RANKING block. The parser depends on this format.

Responses (anonymized — you do NOT know which model wrote which):

Response A:
<<<contents of one of the /tmp/think-*.md files>>>

Response B:
<<<contents of one of the /tmp/think-*.md files>>>

Response C:    [omit if COUNCIL_SIZE == 2]
<<<contents of one of the /tmp/think-*.md files>>>

Rank them on the COMBINATION of three criteria:
1. CHALLENGES MY ASSUMPTIONS — does it surface something I didn't already believe?
2. NAMES TRADE-OFFS — does it identify what's lost by its recommendation?
3. IS HONEST — does it admit what it doesn't know? Does it avoid sycophancy?

Output format — exactly this, nothing else:

FINAL RANKING:
1. Response <letter>
2. Response <letter>
3. Response <letter>    [omit if COUNCIL_SIZE == 2]
```

Parse the ranking, de-anonymize using the saved mapping, store for Phase 4.

**Honest framing of the anonymization:** In a single-orchestrator session, Opus chair could plausibly recognize its own subagent's voice. The shuffle is best-effort, not perfect blinding. A v2 with separate backend processes would be the real fix.

---

## Phase 4: CHAIR_SYNTHESIS (Opus inline — the load-bearing output)

Opus (inline) writes the synthesis the user will actually read. Adaptive thinking is on — this is what justifies the whole command.

Prompt to Opus:

```text
You are the chair of an LLM council. You have:
- The user's original question.
- The user's persona card (~/.claude/USER.md), verbatim.
- N=$COUNCIL_SIZE responses, each with a "What I might be wrong about" section.
- The peer-review ranking (if N >= 2).
- The de-anonymized mapping (which model said what).

Produce the synthesis. MUST contain these sections, in this order:

## Convergent view
1-3 paragraphs. What did the council agree on? State it plainly. If there is NO convergence, say so plainly — do not manufacture agreement.

## Strongest dissenting take
Name one council member's view that disagrees with the convergent view and articulate why it might be right. Even if it's a minority view. Even if the peer review ranked it last. (If --solo, replace this with "Strongest steel-man against my own answer.")

## What you might be wrong about — about the FRAMING, not the answer
Don't tell the user "you might be wrong about Y." Tell the user "the way you ASKED the question presumes X, and X might be false because…" Be specific. Quote their question if it helps.

## Concrete next moves (1-3 items, or "do nothing" if that's right)
Each move:
- Actionable within 7 days
- Cheap to verify or reverse
- NOT a meta-move ("think about it more" is forbidden)

If the right answer is "do nothing — you're already on the right path" or "this is a vent, not a decision," say so plainly. Do not invent action items to look helpful.

## Council provenance
- Opus (first-principles + steel-man): ranked #<N> by peers, key contribution: <one line>
- Codex (contrarian/inversion): ranked #<N>, key contribution: <one line>   [skip if unavailable]
- Antigravity (expansionist/analogy): ranked #<N>, key contribution: <one line>   [skip if unavailable]

---

Anti-sycophancy reminder (applies to YOUR synthesis, not just the council members'):
- If the convergent answer is "you're right, keep going," that's allowed ONLY if at least one council member actively challenged it and lost. Otherwise it's theatrical consensus — flag it.
- If you find yourself writing soothing language, stop and ask: would the user prefer "I don't know" here?
- "User frustration with honest 'not done' is BETTER than false 'done'." (CLAUDE.md, Pillar 1.)
```

---

## Phase 5: OUTPUT

### 5a. Write the full deliberation file

```bash
mkdir -p .claude/research
```

Write `.claude/research/think-${SLUG}.md` (or `.claude/research/think-${ORIGINAL_SLUG}-nudge-$(date +%s).md` if `--nudge`). Template:

```markdown
# Council deliberation: <TOPIC>

think v1 (08-jun-2026)
Generated: <YYYY-MM-DD HH:MM>
Council size: <N> (Opus + [Codex] + [Antigravity])
Mode: <default | --solo | --nudge from think-<prev-slug>.md>
Degradation: <DEGRADE_NOTE or "none">

---

## Synthesis (the only section surfaced in chat)

### Convergent view
<<<from Chair>>>

### Strongest dissenting take
<<<from Chair — named, even if minority>>>

### What you might be wrong about (about the framing)
<<<from Chair>>>

### Concrete next moves
<<<from Chair>>>

### Council provenance
<<<from Chair>>>

---

## Per-agent raw views (de-anonymized)

### Opus — First Principles + Steel-Man
<<<verbatim /tmp/think-opus.md>>>

### Codex — Contrarian / Inversion       [if available]
<<<verbatim /tmp/think-codex.md>>>

### Antigravity — Expansionist / Analogy   [if available]
<<<verbatim /tmp/think-agy.md>>>

---

## Peer review ranking   [if council size >= 2]

Chair (Opus) ranked the anonymized responses:
<<<verbatim FINAL RANKING block>>>

De-anonymized mapping:
- Response A = <agent name>
- Response B = <agent name>
- Response C = <agent name>   [if N == 3]

---

## Provenance

- Topic: <TOPIC>
- Council members invoked: <list with availability status>
- USER.md last modified: <stat -f %Sm ~/.claude/USER.md>
- Anti-sycophancy directives applied: ✓ "wait a minute" opener · ✓ "what I might be wrong about" closers · ✓ chair framing critique
- Failure modes declared up-front: <DEGRADE_NOTE or "none">

---

## Chat surface (what the user saw)

This is a thinking tool, not therapy. The output is opinion, not fact — no EXIT_CODE applies. Use with judgment.
```

### 5b. Surface synthesis in chat (synthesis-only, per user choice)

In-chat output is ONLY:
1. The first-line banner: `think v1 (08-jun-2026)`
2. (If degraded) the `DEGRADE_NOTE` line
3. The full `## Synthesis` block from the file (4 sub-sections + provenance)
4. The clickable link:

```markdown
**Full deliberation**: [think-<slug>.md](.claude/research/think-<slug>.md)
```

5. The one-line timing receipt (see "Timing receipt" below)

No raw per-agent views, no rankings — those live in the file.

### Timing receipt (always-on, total wall time)

Compute the total from the setup ledger (`T_LEDGER`) and print the one-line receipt as the last in-chat line. If the path was lost, recover the newest run (RUN_IDs are UTC stamps, so lexical sort = chronological); if no ledger exists, print the `UNVERIFIED` line — measured, never estimated.

```bash
LEDGER="$T_LEDGER"
[ -f "$LEDGER" ] || LEDGER=$(find .claude/temp/think -name started.txt -type f 2>/dev/null | sort | tail -1)
if [ -z "$LEDGER" ] || [ ! -f "$LEDGER" ]; then
  echo "⏱ think | TOTAL UNVERIFIED (start stamp not found)"
else
  S=$(sed -n 1p "$LEDGER"); SH=$(sed -n 2p "$LEDGER")
  E=$(date +%s); EH=$(date '+%Y-%m-%d %H:%M:%S'); T=$((E - S))
  if [ "$T" -ge 3600 ]; then H=$(printf '%dh %02dm %02ds' $((T/3600)) $((T%3600/60)) $((T%60)));
  else H=$(printf '%dm %02ds' $((T/60)) $((T%60))); fi
  echo "⏱ think | $SH → $EH | TOTAL $H"
fi
```

### 5c. Completion language

This command produces non-verifiable output (opinion, not fact). Forbidden words in the chat surface: "Done", "Fixed", "Complete", "Tests pass", "It works". Use **"Deliberation written to `.claude/research/think-<slug>.md`."** (factual, not a completion claim). Per CLAUDE.md, the EXECUTION_BLOCK requirement is N/A for non-verifiable outputs — declare this in the provenance instead.

---

## Degradation Rules (single source of truth)

| Condition | Behavior | User-facing line |
|---|---|---|
| Codex MCP namespace not loaded | Continue with Opus + Agy | `Council ran with 2 agents (Codex unavailable).` |
| `mcp__agy__agy_ask` tool not loaded | Continue with Opus + Codex | `Council ran with 2 agents (Antigravity unavailable: agy bridge MCP not loaded).` |
| `mcp__agy__agy_ask` errors or exceeds `timeout_s` | Continue without | `Antigravity bridge call failed/timed out. Council degraded.` |
| Both external EIs unavailable | Continue Opus-only, label as auto-solo | `Both external EIs unavailable. Running auto-solo mode.` |
| `~/.claude/USER.md` missing | STOP, write template, halt | `Created template at ~/.claude/USER.md. Open it, fill in, then re-run.` |
| `--solo` flag passed | Skip Phases 2-codex, 2-agy, 3 | `SOLO mode: Opus only. No peer review.` |
| `--nudge` with no prior session | STOP | `--nudge requires a previous /think session.` |
| Output dir missing | `mkdir -p research` silently | (none) |

---

## USER.md Template (written verbatim on first invocation)

Path: `$HOME/.claude/USER.md`. When Phase 0c detects this file is missing, the orchestrator writes this exact content with the `Write` tool, then halts with the user-facing instruction.

```markdown
# About me — persona card for the /think council

This file is injected verbatim into every council member's prompt. Opus, Codex (OpenAI), and Antigravity (Google) will all see it. Be deliberate about what you put here.

**Privacy:** do NOT include passwords, financials, credentials, or anything you wouldn't share with all three providers. This is a summary, not a journal. 200-500 words is the sweet spot. Update by hand when life changes.

---

## Role / current focus
[2-3 lines: what you do, what you're working on this season]

## Values I'm trying to hold to
[3-7 lines, your words — not generic. "Honesty over comfort" beats "be a good person".]

## Active situations (decisions in motion)
- [Dated bullet: "decision pending on X (due: YYYY-MM-DD)"]
- ["in motion on Y (started: YYYY-MM-DD)"]
- ["stuck on Z since: YYYY-MM-DD"]

## Documents the council CAN quote from
- [Optional path: ~/journals/2026/, only if you want it read]
- (Empty = persona card only. Recommended for v1 — the --vault flag is deferred.)

## Anti-sycophancy preferences (the council reads this verbatim)
- I want disagreement, even when uncomfortable.
- I don't want validation unless it has been earned by a real argument.
- I prefer "I don't know" over a confident guess.
- If my framing is wrong, tell me — don't answer a slightly-different question to be polite.

## Topics where I want extra honesty (optional)
[Free-form. e.g. "career decisions" / "relationships" / "anything involving money"]

## Last updated
YYYY-MM-DD
```

---

## User's Topic

$ARGUMENTS
