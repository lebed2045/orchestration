# Research: Claude Opus 4.8 (1M) — Context-Utilization Degradation Threshold

Generated: 2026-06-10
Model under study: `claude-opus-4-8[1m]` (Opus 4.8, 1M-token context variant)
Agents: Opus (web + synthesis) + Codex MCP (official-docs grounding)
Question: At what **% of context used** does Opus 4.8 1M start to lose intelligence ("context rot")?

---

## ⚠️ Bottom Line (read this first)

**There is NO official Anthropic-published "IQ degrades at X%" threshold for Opus 4.8 1M.**
Anyone who gives you a single hard number for *this exact version* is extrapolating. Confirmed by
checking Anthropic's official model/context/compaction docs — they state accuracy/recall degrade as
context fills, but publish no degradation curve or percentage.

The most defensible operational answer, combining the one official signal with the general research.
**These bands match the live Claude Code footer** (`~/.claude/statusline.sh`, copied to
[`.claude/reference/statusline.sh`](statusline.sh)), which colors context as a **percentage of the
window** so it behaves identically on a 200K or a 1M window:

| Footer color | % of window | Tokens @1M | What to expect |
|------|-------------|-----------|----------------|
| 🟢 green | 0–15% | 0–150K | Safe. Full quality through Anthropic's default compaction trigger (150K). |
| 🟡 yellow | 15–25% | 150–250K | Degradation onset for reasoning-heavy / multi-hop work. |
| 🟠 orange | 25–50% | 250–500K | Measurably degrading — compact/retrieve here. |
| 🔴 red | 50–100% | 500K–1M | Ceiling, not a working budget; approaching the self-reported "ineffective" range. |

How this maps to the raw research anchors: Chroma's ~50K rot-onset and Anthropic's 150K compaction
default both sit in green/early-yellow; the footer warns conservatively at the **150K compaction line
(15%)** rather than the earliest-possible 50K, and redlines at **50%** — comfortably before the ~400K
self-reported "ineffective" ceiling (claude-code#34685).

**Practical rule of thumb:** stay 🟢 (**under ~150K / 15%**) for high-precision reasoning/agentic work;
**25% (orange)** is the compact/retrieve line; **50% (red)** is the hard "start fresh" ceiling.
This is engineering guidance, NOT a measured Opus-4.8 rot threshold.

---

## Opus 4.8 1M — What IS published (specific findings)

### The one official anchor: compaction defaults
Anthropic's server-side **compaction triggers at 150,000 input tokens by default** (min configurable
trigger 50,000). On a 1M window that's **15% default / 5% minimum**. This is a *product default*, not a
quality-degradation measurement — but it's the only Opus-4.8-era number Anthropic actually ships.
→ [Anthropic compaction docs](https://platform.claude.com/docs/en/build-with-claude/compaction)

### Long-context benchmark scores (Opus 4.8 launch)
GraphWalks (long-context graph retrieval), Opus 4.8:

| Benchmark | 256K subset | 1M subset | Drop 256K→1M |
|-----------|-------------|-----------|--------------|
| GraphWalks BFS | 85.9% | 68.1% | −17.8 pts |
| GraphWalks Parents | 99.3% | 83.3% | −16.0 pts |

So even on 4.8, going from 256K → 1M costs ~16–18 points. Big improvement vs 4.7 (BFS 1M was 40.3%),
but the **edge-of-window degradation is real and measured**.
→ [llm-stats Opus 4.8 launch](https://llm-stats.com/blog/research/claude-opus-4-8-launch)
→ [digitalapplied Opus 4.8 benchmarks](https://www.digitalapplied.com/blog/claude-opus-4-8-release-dynamic-workflows-2026)

### Official + community framing
- Anthropic: Opus 4.8 improves "long-context handling," "fewer compactions," "better compaction recovery" — but **no degradation curve**. → [Opus 4.8 what's-new](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8)
- "Treat the advertised 1M context as a **ceiling, not a working budget**."
- CodeRabbit (hands-on): visible degradation **past ~200K tokens** in practice.

### Closest thing to a "%" number — but it's the PREDECESSOR (4.6), anecdotal
A GitHub issue on the 1M variant of **Opus 4.6** (not 4.8) reports self-observed degradation:
- **~20%**: started losing track of earlier decisions / circular reasoning
- **~40%**: auto-compaction kicked in; Claude self-reported "0.4–0.5 = degrades noticeably, 0.6 = worse, 0.8+ = rough"
- **~48%**: Claude recommended a fresh session ("not being effective"), i.e. effective high-quality context ≈ **400K not 1M**

⚠️ This is **Opus 4.6**, self-reported/anecdotal, and the issue was **closed as not-planned**. Opus 4.8
specifically claims improved long-context handling, so 4.8 should do *better* than these numbers — treat
40–48% as a pessimistic floor for the previous generation, not a measurement of 4.8.
→ [claude-code issue #34685](https://github.com/anthropics/claude-code/issues/34685)

---

## General Long-Context Degradation Research (the giants)

The phenomenon is real, universal, and **continuous (no cliff)** — degradation starts well before the
advertised limit on every frontier model tested.

- **Chroma "Context Rot"** (18 frontier models incl. Claude 4 / GPT-4.1 / Gemini 2.5): all degrade as
  input grows, even on simple tasks. At **~50% of max context (~64K) F1 ≈ 0.302**, a 45.5% drop from the
  stable region. Position matters ("lost in the middle"): accuracy 70–75% at the ends → 55–60% mid-context.
  → [Chroma Context Rot](https://www.trychroma.com/research/context-rot)
- **NoLiMa** (lexical-match removed): effective context is a *tiny* fraction of advertised. Claude 3.5
  Sonnet listed as **200K claimed / 4K effective (~2%)**; at 32K most models fall to ≤half of baseline.
  → [NoLiMa arXiv 2502.05167](https://arxiv.org/abs/2502.05167)
- **RULER** (NVIDIA, real long-context tasks vs vanilla needle): effective context **~50–65% of
  advertised** for stronger models; a 200K model often unreliable around 130K. Weaker models far worse
  (some <4K usable on a 1M claim).
  → [RULER arXiv 2404.06654](https://arxiv.org/abs/2404.06654)
- **Needle-in-a-haystack** alone *overestimates* real long-context reasoning — RULER/NoLiMa/Chroma all
  show vanilla NIAH looks near-perfect while reasoning tasks collapse. Don't trust NIAH sweeps.

---

## Why "% of window" is a weak metric (important caveat)

- A 32K test is **25% of a 128K model but only 3.2% of a 1M model** — same tokens, very different %.
  Degradation tracks *absolute tokens + task type* more than raw percentage.
- What actually drives rot: task type (literal lookup survives deep; multi-hop reasoning fails early),
  distractors, lexical overlap, needle position, output length, tool-call traces, image tokens.
- **Literal retrieval** can stay useful to 25–50% of window; **ambiguous retrieval / multi-hop reasoning /
  long agentic sessions** degrade much earlier (often <15%).

---

## Recommended Approach (for our orchestration workflows)

1. **Budget, don't fill.** Stay green (<15% / <150K active tokens on 1M) for `/wf`, cops, and
   reasoning-heavy agents. The footer turns yellow at 15% — that's your live gauge.
2. **Compact/retrieve when the footer goes orange (25%).** Past this, summarize → fresh context rather
   than pushing toward 1M. Red (50%) is the hard "start a new session" line.
3. **Never treat 1M as a working budget** — it's a ceiling for occasional whole-corpus passes, not steady state.
4. **Watch task type, not just %.** Multi-hop/agentic work: be stricter (degrade <15%). Single-shot literal
   lookup over a big doc: you can go deeper.
5. If you need a *measured* 4.8 number, you'd have to run RULER/NoLiMa against `claude-opus-4-8[1m]`
   yourself — no one has published one for this exact version.

---

## Sources

| Source | Key contribution |
|--------|------------------|
| [Anthropic compaction docs](https://platform.claude.com/docs/en/build-with-claude/compaction) | 150K default / 50K min compaction trigger (only official 4.8-era number) |
| [Anthropic context-windows docs](https://platform.claude.com/docs/en/build-with-claude/context-windows) | Official: accuracy/recall degrade as context fills |
| [Opus 4.8 what's-new](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8) | Improved long-context, but no curve published |
| [llm-stats 4.8 launch](https://llm-stats.com/blog/research/claude-opus-4-8-launch) | GraphWalks 68.1% @1M vs 85.9% @256K |
| [digitalapplied 4.8](https://www.digitalapplied.com/blog/claude-opus-4-8-release-dynamic-workflows-2026) | "ceiling not a working budget"; 4.7→4.8 long-context gains |
| [claude-code #34685](https://github.com/anthropics/claude-code/issues/34685) | (4.6, anecdotal) degrade ~40%, restart ~48%, effective ≈400K |
| [Chroma Context Rot](https://www.trychroma.com/research/context-rot) | 18 models, continuous degradation, ~45% drop at 50% context |
| [NoLiMa](https://arxiv.org/abs/2502.05167) | Effective context ~2% of advertised when lexical match removed |
| [RULER](https://arxiv.org/abs/2404.06654) | Effective context ~50–65% of advertised on real tasks |
| [`.claude/reference/statusline.sh`](statusline.sh) | The live footer; colors context percent-based — green <15% / yellow 15–25% / orange 25–50% / red ≥50% |

### Agent contributions
- **Opus**: web search sweep, source-fetch, synthesis, our-workflow mapping
- **Codex MCP**: official Anthropic docs grounding (compaction/context/model docs), distinguishing measured vs extrapolated
