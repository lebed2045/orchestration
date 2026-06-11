# Code-Quality Metrics — Measurable Thresholds for Vibe-Coding

**Purpose:** A small set of *cheap, deterministic* code properties, **graded by the evidence behind them**, used by the `/wf` Phase-8a signals pass and the **metrics-cop**. This is the reference; the cop + Phase 8a are the enforcers.

**Why this exists:** Per-edit advisory checks are *incremental-blind* — a class can creep to 1100+ LOC across sessions with no single gate firing. We still *measure* absolute state vs the run baseline to catch that. **But** (v19) we no longer *hard-block* on it: see the evidence note below.

**Evidence note (v19 — important):** A research pass ([`ai-generated-code-best-practices.md`](../research/ai-generated-code-best-practices.md)) found that the gates most people enforce are the *least* evidence-backed:
- **Hard file-size caps** (300/500/600) have **no empirical basis** as a defect predictor — they're a reviewability heuristic. → **WARN, not BLOCK.**
- **Cyclomatic complexity ≈ 0.93·LOC** (Jay et al.) — almost no signal independent of size. → **context only, never a sole block.**
- The **evidence-backed** levers are **small batch size** (DORA 2024: large changesets → −7.2% delivery stability) and **low duplication** (GitClear: AI ~4× clones). → **these are the hard gates.**

So thresholds below are *tiered*: 🟢 evidence-backed (hard-block-worthy), 🟡 plausible heuristic (warn/judge), 🔴 folklore/redundant (don't gate on).

---

## The metric set

| Metric | Tier | Cheap measurement | Warn | Block | Gate class |
|---|---|---|---:|---:|---|
| **Batch size** (changed LOC: added+deleted this run vs baseline) | 🟢 | `git diff --numstat $BASELINE_SHA` | >400 | >800 | **HARD** — the strongest AI-era lever (DORA) |
| **Duplicate code** | 🟢 | `jscpd`; PMD CPD | >3% | >5% / large block | **HARD** (egregious only) — agents patch one clone, miss the other (GitClear) |
| **New suppressions / type holes** | 🟢 | `rg 'eslint-disable\|ts-ignore\|type:\s*ignore\|@SuppressWarnings'` on the diff | any new | >2 new, or unexplained | **HARD** — removes the guardrails an agent relies on |
| **Dependency cycles** | 🟢 | `madge --circular`; `dependency-cruiser` | any test-only cycle | any prod cycle | **HARD** — cycles destroy locality |
| **File SLOC** (absolute, per touched file) | 🟡 | `scc`/`cloc`; fallback `grep -cvE '^\s*$'` | >300 | — | **WARN / judge** — reviewability heuristic, *not* a defect predictor; no hard cap |
| **Function / method SLOC** | 🟡 | `lizard`; `eslint max-lines-per-function` | >50 | — | **WARN / judge** — split only if it does >1 thing |
| **Max nesting depth** | 🟡 | `lizard`; `eslint max-depth` | >3 | — | **WARN / judge** — prefer guard clauses |
| **Parameter count** | 🟡 | `lizard`; `eslint max-params` | >4 | — | **WARN / judge** — hidden coupling smell |
| **Cyclomatic / cognitive complexity** | 🔴 | `lizard`; `radon cc`; sonar | report | — | **CONTEXT ONLY** — CC≈0.93·LOC, redundant; never a sole block |

**Preferred universal tool:** [`lizard`](https://github.com/terryyin/lizard) (`pip install lizard`) — one pass gives function length, CCN, param count across ~15 languages. Plus [`jscpd`](https://github.com/kucherenko/jscpd) for duplication (the 🟢 gate worth installing). Fall back to `scc`/`cloc` for file SLOC, pure-bash heuristics if neither is installed.

---

## Batch size & file size — measured vs baseline (the cumulative view)

Both 🟢 batch size and 🟡 file size are measured against the **run baseline SHA** captured in `/wf` Phase 1 (`git diff $BASELINE_SHA`), so they reflect the **whole run cumulatively**, not a single edit — this is what defeats the incremental-blind problem.

- **Batch size** (`changed LOC` = added+deleted, summed over touched files): WARN >400, **BLOCK >800**. This is the only *size-derived* hard gate, because it's the one with empirical support (DORA: large batches → instability). (Duplication also hard-blocks, but that's a clone signal, not size.)
- **File size** (absolute SLOC per touched file): **WARN only** at >300 (test/fixture ×1.5). It never blocks on its own. A loud warning that prompts the reviewer / metrics-cop to *judge* whether a split is warranted — a cohesive 700-line file may be fine; a 250-line file doing five things is not.

The old "grandfather rule" (block when over-limit AND growing) is **retired** — it hard-blocked on file size, which the evidence doesn't support. The cumulative measurement remains; only the verdict changed from BLOCK to WARN.

---

## What hard-blocks vs what's judged vs what's ignored

- **Hard-block (🟢 deterministic):** egregious batch size, egregious duplication, new unexplained suppressions, new prod import cycles. Numbers, not opinions.
- **Judge (🟡):** file/function size, nesting, params. Surfaced as WARNs; the metrics-cop *agent* recommends an extraction (and must name it) when a file does >1 thing — but **does not block on size**. Architectural REJECTs belong to coherence-/simplicity-cop, not a line-count.
- **Ignore as a gate (🔴):** cyclomatic/cognitive complexity — report for context, never the sole reason to fail (redundant with size).

Never fabricate a number. If no tool is available to measure a row, report `unmeasured` — do **not** guess.

---

## Longitudinal enforcement (v24)

Per-run gates are memoryless; these mechanisms add memory across runs. **Caveat up front:** these are entropy-bound *policies* for AI-context ergonomics, not defect-evidence claims; ratchets can be gamed by mechanical splitting — the cop adjudication layer stays on top.

### Ratchet ledger (`.claude/metrics/ratchet.tsv`, versioned, append-only)

Each `/wf` run appends one row in Phase 9: `run_id<TAB>dup_pct<TAB>suppressions<TAB>prod_cycles<TAB>files_over_warn`. Phase 8a compares the current repo-wide state against the **last** row:

| Metric | Tolerance vs last row | Class |
|---|---|---|
| Repo-wide duplication % (jscpd) | > last + 0.5pt → REJECT | **hard** |
| Suppression count (git grep, `:!*.md` `:!tests/`) | > last → REJECT | **hard** |
| Prod import cycles (madge) | > last → REJECT | **hard** |
| `files_over_warn` (tracked source files >300 SLOC) | — | **trend-only** (gardener input, never blocks) |

**NA honesty rule:** an unmeasured metric (tool missing — jscpd/madge are optional) is recorded as `NA`, reported loudly, and skipped in comparisons — never treated as a pass and never guessed.

### Debt ledger (`.claude/metrics/debt.tsv`, versioned, append-only)

Every Phase 8a SIZE WARN appends `run_id<TAB>file<TAB>sloc`. **3-strikes rule:** a file warned on 3 consecutive appearances with pairwise non-decreasing SLOC → REJECT until it shrinks below the warn threshold or a waiver row is recorded. Waiver format: `<run_id>\t<file>\twaiver:<reason>` (resets the streak); a file dropping below warn appends `recovered:<n>` (also a streak breaker). This converts repeated warnings from wallpaper into a time-bound obligation without reintroducing hard size caps.

**Known limitation:** the deterministic debt gate is scoped to production source as filtered by Phase 8a — markdown workflow files (this repo's "source") are excluded from it by the generic `*.md` filter; their size/trend is owned by metrics-cop judgment and the gardener, not the deterministic gate. This avoids blocking on prose length, which would be a folklore gate.

### Gardener cadence

`/gardener` (manual, or scheduled) reads both ledgers, runs a repo-wide duplication/dead-code sweep, ranks escalated debt first, and executes the top-K extractions as small `/wf`-style tasks with separate commits.

---

## Scope & exemptions

- Apply to **production source touched this run**. Exempt: generated/vendor/`node_modules`/snapshots/migrations, and allow **1.5×** limits for test/fixture files.
- Language-agnostic by design — thresholds are defaults; a project may override via its own config.

---

## Sources

- [ESLint `max-lines`](https://eslint.org/docs/latest/rules/max-lines), [`max-lines-per-function`](https://eslint.org/docs/latest/rules/max-lines-per-function), [`max-depth`](https://eslint.org/docs/latest/rules/max-depth), [`max-params`](https://eslint.org/docs/latest/rules/max-params)
- [SonarSource — metric definitions](https://docs.sonarsource.com/sonarqube-server/2025.4/user-guide/code-metrics/metrics-definition)
- [Radon CC ranks](https://radon.readthedocs.io/en/latest/api.html), [Checkstyle NPath](https://checkstyle.sourceforge.io/checks/metrics/npathcomplexity.html)
- [Microsoft — cyclomatic complexity & maintainability index](https://learn.microsoft.com/en-us/visualstudio/code-quality/code-metrics-cyclomatic-complexity)
- [arc42 Quality Model — code complexity](https://quality.arc42.org/qualities/code-complexity)
- [getDX — why CC alone misleads (cognitive complexity)](https://getdx.com/blog/cyclomatic-complexity/)
- [Right-sizing files for AI code editors — 150–500 LOC](https://medium.com/@eamonn.faherty_58176/right-sizing-your-python-files-the-150-500-line-sweet-spot-for-ai-code-editors-340d550dcea4)
- [`lizard` — language-agnostic complexity analyzer](https://github.com/terryyin/lizard)
