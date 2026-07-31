# /think — Council of Opus + Codex + Antigravity. Independent, peer-reviewed, cross-examined, anti-sycophantic.

**Updated:** `21-jul-2026` · **Tag:** `[council-default | peer-review | cross-examination | anti-syco | persona-card]`

**First line of every run must be, verbatim:** `think (21-jul-2026)` — update the date above when the deliberation logic changes.

A third primitive next to `/wf` (do) and `/r` (find): for open / introspective / "what do you think?" questions where there is no objective ground truth. Implements **Karpathy's LLM Council** (independent parallel views → anonymized peer review → adversarial cross-examination → chair synthesis) with **forced reasoning-method diversity** (ngmeyer/council-review). Anti-sycophancy is load-bearing, not decorative.

## Usage

```bash
/think <topic>                       # default: 3-agent council, peer review, then cross-examination
/think --solo <topic>                # Opus only — fast, no peer review or cross-examination
/think --nudge "<pushback>"          # re-deliberate on most-recent think-*.md with new context
/think --vault <path> <topic>        # OPT-IN journal RAG — not yet implemented
```

**Default behavior:** all three EIs first answer independently in parallel. If at least two members succeed, anonymous peer review and adversarial cross-examination both run automatically before synthesis. There is no debate flag: cross-examination is the point of `/think`, not an optional mode. The `-cg` is not an opt-in here either. Flags subtract.

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

# --vault <path> (not yet implemented)
if [[ "$TOPIC" == *"--vault"* ]]; then
  VAULT_PATH=$(echo "$TOPIC" | sed -n 's/.*--vault[[:space:]]\+\([^ ]*\).*/\1/p')
  TOPIC="${TOPIC//--vault $VAULT_PATH/}"
  echo "[INFO] --vault is documented but NOT implemented yet. Ignoring '$VAULT_PATH'. Persona card only."
fi

TOPIC="${TOPIC## }"; TOPIC="${TOPIC%% }"

# Slug from topic (mirrors r.md convention)
SLUG=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | cut -c 1-60)
[ -z "$SLUG" ] && SLUG="think-$(date +%s)"
# Timing ledger (always-on). Total wall time is computed from this file at completion; never estimated.
T_RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)                  # UTC stamp; lexical sort == chronological
mkdir -p .claude/temp/think
T_DIR=$(mktemp -d ".claude/temp/think/${T_RUN_ID}-XXXX")
T_LEDGER="$T_DIR/started.txt"
{ date +%s; date '+%Y-%m-%d %H:%M:%S'; } > "$T_LEDGER"   # line 1 = epoch, line 2 = human start

select_think_output() {
  OUTPUT="$1.md"
  while stat "$OUTPUT" >/dev/null 2>&1; do
    # The current proposal exists. Generate a fresh collision-proof run ID, then loop so
    # stat explicitly probes the fallback proposal too before it can be selected.
    T_COLLISION_RUN_DIR=$(mktemp -d "$T_DIR/artifact-XXXX")
    T_COLLISION_RUN_ID="$(basename "$T_DIR")-$(basename "$T_COLLISION_RUN_DIR")"
    OUTPUT="$1-${T_COLLISION_RUN_ID}.md"
  done
}

OUTPUT=""
[ -z "$NUDGE" ] && select_think_output ".claude/research/think-${SLUG}"

echo "TOPIC: $TOPIC"
echo "SOLO: $SOLO"
[ -n "$OUTPUT" ] && echo "OUTPUT: $OUTPUT"
[ -n "$NUDGE" ] && echo "NUDGE: $NUDGE"
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
# AGY_AVAILABLE=true iff mcp__agy__agy_ask is loaded or ~/.local/bin/agy-ask is executable
```

Use `mcp__agy__agy_ask`; if it is not exposed, use `~/.local/bin/agy-ask`. The repository-owned bridge tries `agy` first and the configured local Gemini-compatible fallback second. Model selection is owned by the bridge. Never substitute raw `agy`, `gemini`, a browser, Vertex, or Gemini API.

The repository-owned bridge owns model selection and routing. It tries AGY first, then auto-routes to the configured local Gemini-compatible fallback and prefixes the response with the actual route. Either route is a valid Gemini council response, not a downgrade; do not substitute Codex/self-deliberation. Restart Claude Code after bridge updates.

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

CROSS_EXAM_STATUS="pending"
if [ "$SOLO" = "true" ]; then
  CROSS_EXAM_STATUS="skipped: --solo leaves only one successful council member"
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
The original topic is reconstructed from `$PREV` (first `## Council deliberation: <TOPIC>` line). The nudge text is appended as additional context for the new round. Derive its slug, then use the same stat-and-retry selector as a normal run; never overwrite the previous deliberation:

```bash
ORIGINAL_SLUG=$(echo "$ORIGINAL_TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | cut -c 1-60)
select_think_output ".claude/research/think-${ORIGINAL_SLUG}-nudge"
echo "OUTPUT: $OUTPUT"
```

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

Spawn the council members **in a single message with multiple tool calls** so they run concurrently. Each gets the **shared preamble** + their **assigned reasoning method**. Capture each output to `$T_DIR/<agent>-r1.md` for Phase 3. Keep the returned Opus agent ID, Codex conversation ID, and Antigravity route/provenance for the cross-examination round when the transport supplies them.

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

Capture to `$T_DIR/opus-r1.md`.

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

Capture the tool response to `$T_DIR/codex-r1.md`.

### 2c. Antigravity (agy bridge MCP) — Expansionist / Analogy

Call `mcp__agy__agy_ask` with `timeout_s=120`, or `~/.local/bin/agy-ask` when the MCP tool is not exposed. Save the returned final text to `$T_DIR/agy-r1.md`. Both transports enter the same router; no background PID/kill management is needed.

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

The bridge call is synchronous and bounded. If the selected bridge transport errors after its internal fallback or exceeds the timeout, treat agy as unavailable: `AGY_AVAILABLE=false; COUNCIL_SIZE=$((COUNCIL_SIZE - 1))` and continue with the remaining council members.

If the response is truncated, continue with `mcp__agy__agy_continue` or `~/.local/bin/agy-ask continue` before marking the Antigravity pass failed.

### 2d. Successful-member census

After all independent calls settle, count only non-empty round-1 outputs as successful council members. Update `CODEX_AVAILABLE`, `AGY_AVAILABLE`, `COUNCIL_SIZE`, and `DEGRADE_NOTE` from the actual results rather than the preflight probes. A namespace that existed but returned no usable answer is unavailable for all later phases.

Set the cross-examination state from that actual count:

```bash
if [ "$SOLO" = "true" ]; then
  CROSS_EXAM_STATUS="skipped: --solo leaves only one successful council member"
elif [ "$COUNCIL_SIZE" -lt 2 ]; then
  CROSS_EXAM_STATUS="skipped: fewer than two successful council members"
else
  CROSS_EXAM_STATUS="eligible"
fi
```

The first-pass independence guarantee ends only after this census. Do not share any member's answer with another member before Phase 3 has banked the peer-review result.

---

## Phase 3: PEER_REVIEW (skip if COUNCIL_SIZE < 2)

Opus (inline) reads the available responses in **anonymized order**. The orchestrator shuffles letter assignments per session (`A`, `B`, `C`) and keeps the mapping in a local variable for de-anonymization in Phases 4–5.

Prompt to Opus (inline):

```text
You are the chair of an LLM council. You will now anonymously review the responses below.

CRITICAL: Do not write any text other than the FINAL RANKING block. The parser depends on this format.

Responses (anonymized — you do NOT know which model wrote which):

Response A:
<<<contents of one of the $T_DIR/*-r1.md files>>>

Response B:
<<<contents of one of the $T_DIR/*-r1.md files>>>

Response C:    [omit if COUNCIL_SIZE == 2]
<<<contents of one of the $T_DIR/*-r1.md files>>>

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

Parse the ranking, de-anonymize using the saved mapping, and retain both for Phases 4–5.

**Honest framing of the anonymization:** In a single-orchestrator session, Opus chair could plausibly recognize its own subagent's voice. The shuffle is best-effort, not perfect blinding. A future redesign with separate backend processes would be the real fix.

---

## Phase 4: ADVERSARIAL_CROSS_EXAMINATION (default when COUNCIL_SIZE >= 2)

This phase has no flag and is not optional in a multi-member `/think` run. It starts only after the independent first passes and anonymous peer-review ranking are banked. If `CROSS_EXAM_STATUS` is not `eligible`, make no round-2 calls and preserve its exact skip reason in the deliberation artifact and Council provenance.

When eligible, build a **sanitized rival digest for each successful member**. Each digest contains the key claims, reasoning, uncertainty, and peer-review feedback for every *other* successful member, labelled by author. Share conclusions, not raw private context, credentials, or newly discovered secrets. The persona card was already authorized for all council providers, but do not repeat irrelevant personal details. Never include the chair's emerging synthesis: this is member-to-member challenge, not chair anchoring.

Send one round-2 prompt to **every** successful member in parallel:

- **Opus:** continue the Phase 2a subagent by its agent ID when supported; otherwise spawn a fresh `general-purpose` subagent with Opus's own round-1 response plus the rival digest. No `model:` override.
- **Codex:** use `mcp__codex-cli__codex-reply` with the Phase 2b conversation ID when available. If the transport did not return a usable ID, make a fresh `mcp__codex-cli__codex` call containing Codex's round-1 response and rival digest. Never set `model` or `reasoningEffort`.
- **Antigravity:** use `mcp__agy__agy_ask`, or `~/.local/bin/agy-ask` only when the MCP tool is not exposed, with Antigravity's round-1 response and rival digest. The agy bridge continues to own routing and model selection.

Use this prompt body for each member:

```text
The independent first-pass council responses and anonymous peer review are now banked.
This is an adversarial cross-examination, not a consensus exercise. Do not soften a
real objection to be polite, and do not manufacture disagreement where you lack one.

QUESTION:
<<<TOPIC>>>

YOUR round-1 response:
<<<this member's complete round-1 response>>>

RIVAL DIGESTS (sanitized, labelled by author):
<<<key claims, reasoning, uncertainty, and relevant peer-review feedback from every other successful member>>>

Do this in order:
1. Challenge each rival's important claims. Identify what is wrong, unsupported,
   incomplete, or framed too narrowly. Give the concrete reason. If you cannot land an
   evidence-backed or mechanically sound objection, say "no sound rebuttal found".
2. State what each rival caught that you missed. Do not evade a correction.
3. Re-state your own key claims after the challenge. Mark every one [HELD], [REVISED],
   or [WITHDRAWN]. A label without a reason is invalid.

Output exactly these sections:
## Challenges to rivals
## What I missed
## My final position
```

Save successful rebuttals to `$T_DIR/opus-r2.md`, `$T_DIR/codex-r2.md`, and `$T_DIR/agy-r2.md`. A round-2 failure never erases a valid round-1 response: record the member as `no rebuttal output` and use its round-1 position as the latest available position.

After all round-2 calls settle, set:

- `CROSS_EXAM_STATUS="completed: <N>/<COUNCIL_SIZE> rebuttals returned"` when at least one rebuttal returned; append failed member names when partial.
- `CROSS_EXAM_STATUS="attempted: no rebuttal outputs returned"` when every round-2 call failed; synthesize from round 1 and state this degradation plainly.

The chair must use each member's **latest valid position** in Phase 5: round 2 where present, otherwise round 1. `[WITHDRAWN]` retracts only that member's claim; it does not erase a rival's independently held claim. A disagreement that remains `[HELD]` on opposing sides is the highest-value signal and must be surfaced, not averaged away.

---

## Phase 5: CHAIR_SYNTHESIS (Opus inline — the load-bearing output)

Opus (inline) writes the synthesis the user will actually read. Adaptive thinking is on — this is what justifies the whole command.

Prompt to Opus:

```text
You are the chair of an LLM council. You have:
- The user's original question.
- The user's persona card (~/.claude/USER.md), verbatim.
- N=$COUNCIL_SIZE latest valid member positions, using round-2 rebuttals where present and round-1 fallbacks otherwise.
- The peer-review ranking (if N >= 2).
- The de-anonymized mapping (which model said what).
- CROSS_EXAM_STATUS and the HELD / REVISED / WITHDRAWN ledger (if cross-examination ran).

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
- Cross-examination: <exact CROSS_EXAM_STATUS>

---

Anti-sycophancy reminder (applies to YOUR synthesis, not just the council members'):
- If the convergent answer is "you're right, keep going," that's allowed ONLY if at least one council member actively challenged it and lost. Otherwise it's theatrical consensus — flag it.
- If you find yourself writing soothing language, stop and ask: would the user prefer "I don't know" here?
- "User frustration with honest 'not done' is BETTER than false 'done'." (CLAUDE.md, Pillar 1.)
```

---

## Phase 6: OUTPUT

### 6a. Write the full deliberation file

```bash
mkdir -p .claude/research
```

Write to `$OUTPUT`, the no-clobber path selected during setup (or the run-tagged nudge path selected in Phase 0e). Template:

```markdown
# Council deliberation: <TOPIC>

think (21-jul-2026)
Generated: <YYYY-MM-DD HH:MM>
Council size: <N> (Opus + [Codex] + [Antigravity])
Mode: <default | --solo | --nudge from think-<prev-slug>.md>
Degradation: <DEGRADE_NOTE or "none">
Cross-examination: <exact CROSS_EXAM_STATUS>

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

## Per-agent independent views (de-anonymized)

### Opus — First Principles + Steel-Man
<<<verbatim $T_DIR/opus-r1.md>>>

### Codex — Contrarian / Inversion       [if available]
<<<verbatim $T_DIR/codex-r1.md>>>

### Antigravity — Expansionist / Analogy   [if available]
<<<verbatim $T_DIR/agy-r1.md>>>

---

## Peer review ranking   [if council size >= 2]

Chair (Opus) ranked the anonymized responses:
<<<verbatim FINAL RANKING block>>>

De-anonymized mapping:
- Response A = <agent name>
- Response B = <agent name>
- Response C = <agent name>   [if N == 3]

---

## Adversarial cross-examination

Status: <exact CROSS_EXAM_STATUS>

[When attempted, one row per successful round-1 member. Use `no rebuttal output; round-1 fallback` for a failed round-2 call:]

| Member | HELD | REVISED | WITHDRAWN | Strongest challenge landed | Latest-position source |
|---|---|---|---|---|---|

### Opus rebuttal   [if `$T_DIR/opus-r2.md` exists]
<<<verbatim $T_DIR/opus-r2.md>>>

### Codex rebuttal   [if `$T_DIR/codex-r2.md` exists]
<<<verbatim $T_DIR/codex-r2.md>>>

### Antigravity rebuttal   [if `$T_DIR/agy-r2.md` exists]
<<<verbatim $T_DIR/agy-r2.md>>>

---

## Provenance

- Topic: <TOPIC>
- Council members invoked: <list with availability status>
- USER.md last modified: <stat -f %Sm ~/.claude/USER.md>
- Anti-sycophancy directives applied: ✓ "wait a minute" opener · ✓ "what I might be wrong about" closers · ✓ peer review · ✓ adversarial cross-examination when eligible · ✓ chair framing critique
- Cross-examination status: <exact CROSS_EXAM_STATUS>
- Failure modes declared up-front: <DEGRADE_NOTE or "none">

---

## Chat surface (what the user saw)

This is a thinking tool, not therapy. The output is opinion, not fact — no EXIT_CODE applies. Use with judgment.
```

### 6b. Surface synthesis in chat (synthesis-only, per user choice)

In-chat output is ONLY:
1. The first-line banner: `think (21-jul-2026)`
2. (If degraded) the `DEGRADE_NOTE` line
3. The full `## Synthesis` block from the file (4 sub-sections + provenance)
4. The clickable link:

```markdown
**Full deliberation**: [<actual output filename>](<actual `$OUTPUT` path>)
```

5. The factual write receipt: `Deliberation written to <actual $OUTPUT path>.`
6. The one-line timing receipt (see "Timing receipt" below). This is the final in-chat line; emit no trailing text.

No raw per-agent views, no rankings — those live in the file.

### Timing receipt (always-on, total wall time)

Immediately after `Deliberation written to <actual $OUTPUT path>.`, compute the total from the setup ledger (`T_LEDGER`) and print the one-line receipt as the last in-chat line. If the path was lost, recover the newest run (RUN_IDs are UTC stamps, so lexical sort = chronological); if no ledger exists, print the `UNVERIFIED` line — measured, never estimated. Emit nothing after the timing receipt.

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

### 6c. Completion language

This command produces non-verifiable output (opinion, not fact). Forbidden words in the chat surface: "Done", "Fixed", "Complete", "Tests pass", "It works". Use **"Deliberation written to `<actual $OUTPUT path>`."** immediately before the final timing receipt (factual, not a completion claim). Per CLAUDE.md, the EXECUTION_BLOCK requirement is N/A for non-verifiable outputs — declare this in the provenance instead.

---

## Degradation Rules (single source of truth)

| Condition | Behavior | User-facing line |
|---|---|---|
| Codex MCP namespace not loaded | Continue with Opus + Agy | `Council ran with 2 agents (Codex unavailable).` |
| MCP tool not loaded but `agy-ask` exists | Use `agy-ask`; no degradation | Record the bridge route prefix. |
| Both bridge transports missing | Continue with Opus + Codex | `Council ran with 2 agents (Gemini bridge unavailable).` |
| Bridge errors after fallback or exceeds timeout | Continue without | `Antigravity bridge call failed/timed out. Council degraded.` |
| Both external EIs unavailable | Continue Opus-only, label as auto-solo | `Both external EIs unavailable. Running auto-solo mode.` |
| `~/.claude/USER.md` missing | STOP, write template, halt | `Created template at ~/.claude/USER.md. Open it, fill in, then re-run.` |
| `--solo` flag passed | Skip Phases 2b, 2c, 3, and 4 | `SOLO mode: Opus only. Cross-examination skipped: --solo leaves only one successful council member.` |
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
- (Empty = persona card only. Recommended for now — the --vault flag is deferred.)

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
