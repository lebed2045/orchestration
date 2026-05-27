# /sc-audit — Smart Contract Audit Workflow

**Smart contract audit & LP risk assessment.** 6 parallel reviewers (4 Claude + Codex + Gemini), blue team validation, LP risk scorecard.

**Tag:** `[6-parallel | trace-first | red/blue | LP-scorecard | MCP-enhanced]`

**Usage:** `/sc-audit <contract-path-or-repo-description>`

**Output:** `audits/<protocol>-audit-YYYY-MM-DD.md`

**This is a READ-ONLY research workflow. No code changes. No commits.**

---

## Phase Structure (8 Phases)

```
Phase 1: INVENTORY           — Map system (orchestrator)
Phase 2: DEEP TRACE          — Call-path traces (1 Claude, sequential)
Phase 3: PARALLEL AUDIT      — 4 Claude + Codex + Gemini (6 reviewers, parallel)
Phase 4: BLUE TEAM           — Confirm/rebut findings (1 Claude + Gemini tiebreaker)
Phase 5: LP RISK SCORECARD   — Quantitative scoring (orchestrator)
Phase 6: SYNTHESIS           — Unified report (1 Claude)
Phase 7: HUMAN GATE          — Present findings for review
Phase 8: DELIVERABLE         — Write final audit report to file
```

---

## State Tracking

Every response MUST start with:

```text
[SC-AUDIT.PhaseX] [Inventory: SET|UNSET] [Traces: SET|UNSET] [Status: in_progress|blocked|complete]
```

---

## Phase 1: INVENTORY (orchestrator, read-only)

Read all contracts and build the system map. This feeds every subsequent agent.

1. Identify all Solidity files (`.sol`)
2. Map contract inheritance, imports, interfaces
3. Identify external dependencies (oracles, bridges, other protocols)
4. Map all roles and privileges (Ownable, AccessControl, custom modifiers)
5. Detect upgrade patterns (proxy? UUPS? transparent? immutable?)
6. List all public/external functions with signatures
7. Identify token standards (ERC20, ERC721, ERC4626, etc.)
8. Map token/ETH flow paths

**Write output to `.claude/temp/audit-inventory.md`:**

```markdown
# Audit Inventory: [Protocol Name]
Generated: [date]

## Contracts
| File | Contract | LOC | Compiler | Proxy? | Standards |
|------|----------|-----|----------|--------|-----------|

## Inheritance Tree
[text representation]

## External Dependencies
| Dependency | Type | Trust Assumption |
|------------|------|-----------------|

## Roles & Privileges
| Role | Current Holder | Capabilities | Timelock? | Multisig? |
|------|---------------|-------------|-----------|-----------|

## Entry Points
| Function | Contract | Visibility | Access Control | State Changes | External Calls |
|----------|----------|-----------|---------------|--------------|----------------|

## Token Flows
| Flow | Direction | Conditions | Value |
|------|-----------|-----------|-------|
```

**VERIFY**: Show `cat .claude/temp/audit-inventory.md | head -40`

**Do NOT proceed without inventory.**

---

## Phase 2: DEEP TRACE (1 Claude agent, sequential)

One agent traces every public/external function. This is the "how does it work" phase — slow but produces the most valuable artifact.

```bash
claude -p "You are a smart contract analyst with ZERO prior context.
Your job: trace every public/external function call path in detail.

Read:
- All .sol files in the project
- .claude/temp/audit-inventory.md (system map)

For EACH public/external function, document:

### [ContractName.functionName(params)]
- **Access**: [who can call — anyone / onlyOwner / specific role / conditions]
- **Call path**: A.func() → B.func() → C.func() [with file:line references]
- **State read**: [list state variables read]
- **State written**: [list state variables modified]
- **External calls**: [to what contract/address? before or after state update?]
- **Value flow**: [ETH/tokens: direction, amount, recipient]
- **Events**: [what events are emitted]
- **Reverts**: [under what conditions does this revert]
- **Invariant**: [what MUST be true before and after this call]

After tracing ALL functions, extract:

## SYSTEM INVARIANTS
Properties that must hold across ALL functions:
- [e.g., totalSupply == sum(balances[*])]
- [e.g., totalBorrowed < totalCollateral * LTV]
- [e.g., only admin can change fee recipient]

## STATE MACHINE
Valid state transitions and their guards:
- [State A] → [State B]: requires [condition]

## VALUE FLOW SUMMARY
Where does money come in, where does it go out, who controls the paths.

Write ALL output to: .claude/temp/audit-traces.md" \
  --allowedTools Read,Glob,Grep,Bash \
  --print
```

**VERIFY**: Show `cat .claude/temp/audit-traces.md | head -50`

**Do NOT proceed without traces.**

---

## Phase 3: PARALLEL AUDIT (6 reviewers — 4 Claude + Codex + Gemini)

All 6 receive `audit-inventory.md` + `audit-traces.md` + source code. Each has a **distinct mandate and checklist**. All launch simultaneously.

### Step 1: Launch 4 Claude agents (background subprocesses)

#### Claude 1: `exploit-hunter` — Technical Vulnerabilities

```bash
claude -p "You are a smart contract exploit researcher.
Mandate: find every way to steal funds, break invariants, or DoS the system.

Read: all .sol files, .claude/temp/audit-inventory.md, .claude/temp/audit-traces.md

CHECK EVERY ITEM (report N/A if not applicable):
□ Reentrancy (cross-function, cross-contract, read-only reentrancy)
□ Integer overflow/underflow (unchecked blocks, shift operations)
□ Flash loan attack vectors (borrow → manipulate → profit → repay)
□ Signature replay / malleability / permit abuse
□ Front-running / sandwich attack surfaces
□ Unchecked external call return values
□ Storage collision in proxy patterns
□ Denial of service (gas griefing, block stuffing, unbounded loops)
□ Timestamp / block.number manipulation
□ tx.origin vs msg.sender confusion
□ Delegatecall to untrusted contracts
□ Self-destruct / selfdestruct recipient risks
□ Math precision / rounding errors (especially interest/fee calculations)
□ Multi-tx temporal abuse sequences (A then B then C)
□ Compiler version known bugs (check solc version against advisory list)
□ ERC20 approval race condition
□ Return value not checked on low-level calls
□ Uninitialized storage pointers

For each finding output:
---
FINDING: [title]
SEVERITY: [CRITICAL|HIGH|MEDIUM|LOW|INFO]
LOCATION: [file:line]
DESCRIPTION: [what is wrong]
EXPLOIT_SCENARIO:
  1. [step]
  2. [step]
  3. [profit/damage]
RECOMMENDATION: [specific fix]
---

End with:
EXPLOIT_HUNTER_SUMMARY:
  CRITICAL: [count]
  HIGH: [count]
  MEDIUM: [count]
  LOW: [count]
  INFO: [count]" \
  --allowedTools Read,Glob,Grep,Bash \
  --print > /tmp/audit-exploits.txt &
```

#### Claude 2: `admin-abuse-hunter` — Deployer/Admin Rug Pull Vectors

```bash
claude -p "You are an adversarial analyst.
ASSUME the deployer/admin is MALICIOUS.
Find every way they can steal user funds or manipulate the protocol.

Read: all .sol files, .claude/temp/audit-inventory.md, .claude/temp/audit-traces.md

CHECK EVERY ITEM:
□ Owner can drain funds directly (withdrawal, sweep, emergency functions)
□ Owner can set fee/tax to 100%
□ Owner can pause deposits but still withdraw (asymmetric pause)
□ Owner can upgrade implementation to malicious contract
□ Owner can change oracle/price feed to controlled address
□ Owner can whitelist/blacklist addresses arbitrarily
□ Owner can mint unlimited tokens
□ Owner can change critical parameters without timelock
□ Timelock bypass paths (cancel + re-queue, or direct execution path)
□ Multisig threshold too low (1-of-N) or single EOA owner
□ Retained deployer privileges after renounceOwnership
□ Initializer can be called twice (proxy re-initialization)
□ Hidden admin functions (selfdestruct, arbitrary delegatecall)
□ Emergency functions that favor admin over users
□ Upgrade paths that skip timelock or governance vote
□ Token approval patterns that leave protocol with unlimited allowance
□ Admin can front-run user withdrawals
□ Admin can modify reward distribution retroactively

For each finding output:
---
RUG_VECTOR: [title]
SEVERITY: [CRITICAL|HIGH|MEDIUM|LOW]
ATTACK_STEPS:
  1. [admin action]
  2. [admin action]
  3. [funds extracted]
FUNDS_AT_RISK: [estimate or 'all user deposits']
CURRENT_MITIGATION: [what exists, if any]
RECOMMENDED_FIX: [what should be added]
---

End with:
ADMIN_ABUSE_SUMMARY:
  RUG_VECTORS_FOUND: [count]
  CRITICAL: [count]
  HIGH: [count]
  UNMITIGATED: [count]" \
  --allowedTools Read,Glob,Grep,Bash \
  --print > /tmp/audit-admin-abuse.txt &
```

#### Claude 3: `econ-analyst` — Economic & DeFi Risks

```bash
claude -p "You are a DeFi economic risk analyst (Gauntlet/Chaos Labs methodology).
Evaluate the protocol's economic soundness for capital providers.

Read: all .sol files, .claude/temp/audit-inventory.md, .claude/temp/audit-traces.md

CHECK EVERY ITEM:
□ Oracle manipulation (TWAP window too short? single source? flash-loanable?)
□ Oracle staleness (heartbeat check? max age? deviation threshold?)
□ Oracle fallback (what happens if primary oracle goes down?)
□ Price impact attacks (thin liquidity + large position = manipulation)
□ MEV extraction paths (sandwich, JIT liquidity, liquidation racing)
□ Flash loan amplification of any economic attack
□ Impermanent loss exposure and mitigation
□ Reward calculation gaming (deposit-before-reward, withdraw-after)
□ Fee-on-transfer token compatibility
□ Rebasing token compatibility
□ Slippage tolerance exploitation
□ LP token manipulation / liquidity removal rug
□ Death spiral scenarios (de-peg → liquidation cascade → insolvency)
□ Interest rate model soundness (utilization curve, kink points)
□ Liquidation incentive adequacy (is liquidation profitable under stress?)
□ Bad debt accumulation (what happens when collateral < debt?)
□ Collateral concentration risk (one whale = systemic risk)
□ Correlated asset risk (if ETH drops 40%, what cascades?)
□ Sandwich-able interest accrual or reward distribution
□ JIT liquidity attacks on AMM pools

For each finding output:
---
ECON_RISK: [title]
SEVERITY: [CRITICAL|HIGH|MEDIUM|LOW]
ATTACK_SCENARIO: [narrative — who does what, with how much capital]
CAPITAL_REQUIRED: [approximate]
EXPECTED_PROFIT: [approximate or 'protocol insolvency']
LIKELIHOOD: [LOW|MEDIUM|HIGH]
MARKET_CONDITIONS: [what market state triggers this]
---

End with:
ECON_RISK_SUMMARY:
  CRITICAL: [count]
  HIGH: [count]
  DEATH_SPIRAL_RISK: [YES|NO]
  ORACLE_RISK_LEVEL: [LOW|MEDIUM|HIGH]" \
  --allowedTools Read,Glob,Grep,Bash \
  --print > /tmp/audit-economic.txt &
```

#### Claude 4: `ops-risk-analyst` — Governance, Dependencies, Systemic

```bash
claude -p "You are a protocol operations and governance risk analyst.
Evaluate everything that isn't a direct exploit but could still cause loss.

Read: all .sol files, .claude/temp/audit-inventory.md, .claude/temp/audit-traces.md

CHECK EVERY ITEM:
□ Centralization risk (single points of failure, key-person dependency)
□ Governance attack (vote buying, flash-loan governance, quorum capture)
□ Governance timelock enforceability (can it be bypassed?)
□ Dependency risk (external contract upgrades breaking integration)
□ Bridge trust assumptions (multisig? light client? committee?)
□ Chain-specific risks (L2 sequencer downtime, L1 reorg, bridge delay)
□ Compiler version issues (check solc version against known CVEs)
□ Missing event emissions (off-chain monitoring blind spots)
□ Missing input validation on critical parameters
□ Hardcoded addresses / magic numbers
□ Test coverage gaps (functions with no tests)
□ Documentation vs implementation mismatches
□ Lack of circuit breakers / emergency pause
□ Upgrade storage layout compatibility
□ Front-end / supply chain risk (npm deps, DNS, CDN)
□ Incident response readiness (pause mechanism? war room process?)
□ Insurance / backstop fund adequacy
□ Regulatory / sanctions exposure (jurisdiction, KYC requirements)
□ Team operational security (key ceremony, signer distribution)
□ Post-audit code drift (unaudited patches since last audit)

For each finding output:
---
OPS_RISK: [title]
SEVERITY: [CRITICAL|HIGH|MEDIUM|LOW|INFO]
CATEGORY: [governance|dependency|operational|regulatory|systemic]
DESCRIPTION: [what is the risk]
IMPACT: [what happens if this materializes]
RECOMMENDATION: [specific mitigation]
---

End with:
OPS_RISK_SUMMARY:
  CRITICAL: [count]
  HIGH: [count]
  CATEGORIES_AFFECTED: [list]
  CENTRALIZATION_LEVEL: [LOW|MEDIUM|HIGH|EXTREME]" \
  --allowedTools Read,Glob,Grep,Bash \
  --print > /tmp/audit-ops-risk.txt &
```

### Step 2: Launch Codex + Gemini (MCP, parallel — same message)

**MUST call BOTH tools in a single message for parallel execution.**

**Tool 1: Codex** — Call `mcp__codex-cli__codex`:

| Parameter | Value |
|-----------|-------|
| prompt | See below |
| workingDirectory | Project root |

```text
You are a smart contract security auditor performing a line-by-line code review.

Read all .sol files in this project, plus:
- .claude/temp/audit-inventory.md (system map with roles, entry points, dependencies)
- .claude/temp/audit-traces.md (call traces, invariants, state machine)

Perform a THOROUGH security review focused on:

1. ACCESS CONTROL: Every external/public function — who can call it? Missing modifiers? Over-permissive roles?

2. REENTRANCY: Any external call before state update? Cross-contract reentrancy via callbacks? Read-only reentrancy through view functions that read stale state?

3. MATH SAFETY: Unchecked blocks, precision loss in division, division before multiplication, shift operation bugs, rounding direction (always round against the user, in favor of protocol)

4. INVARIANT VIOLATIONS: Do the system invariants from audit-traces.md actually hold under all code paths? Can any function break a stated invariant?

5. STORAGE SAFETY: Proxy storage collisions, uninitialized storage pointers, storage layout compatibility across upgrades

6. COMPARATIVE ANALYSIS: Compare patterns against battle-tested implementations (Aave V3, Uniswap V4, OpenZeppelin). Flag any "novel logic" that deviates from established patterns — this is where 90% of bugs live.

7. DEPENDENCY RISK: External contract calls — what assumptions does this code make about the behavior of external contracts? Are those assumptions validated?

Output format:

For each file reviewed:
FILE: [path]
FINDINGS:
  1. [SEVERITY] [line:N] [description]
  2. ...

Then overall:
CODEX_AUDIT_SUMMARY:
  FILES_REVIEWED: [count]
  CRITICAL: [count]
  HIGH: [count]
  MEDIUM: [count]
  LOW: [count]
  NOVEL_LOGIC_FLAGGED: [list of functions that deviate from standard patterns]
  TOP_3_CONCERNS: [ranked list]
```

**Tool 2: Gemini** — Call `mcp__gemini__ask-gemini` (in same message as Codex):

```text
Working directory: [pwd]

You are a DeFi risk analyst using Gauntlet/Chaos Labs methodology.
Evaluate this protocol from the perspective of a Liquidity Provider deciding
whether to deploy capital.

Read: all .sol files, .claude/temp/audit-inventory.md, .claude/temp/audit-traces.md

PERFORM THESE ANALYSES:

1. ECONOMIC STRESS TEST — For each scenario, trace through the actual code
   to determine the outcome:

   A. 40% collateral price drop in 1 hour:
      - Does the liquidation mechanism handle this?
      - Is there enough liquidation incentive?
      - Can bad debt accumulate?
      - What happens to LP positions?

   B. Oracle goes stale for 30 minutes:
      - Is there a staleness check? What's the max age?
      - What operations continue with stale prices?
      - Can an attacker exploit stale prices?

   C. Largest depositor exits in one transaction:
      - Slippage impact on remaining LPs?
      - Does the protocol remain functional?
      - Any withdrawal queue or cooldown?

   D. Flash loan + oracle manipulation combo:
      - Maximum extractable value?
      - Is TWAP used? How long is the window?
      - Can spot price be manipulated profitably?

   E. Correlated market crash (ETH -50%, all alts -70%):
      - Protocol solvency under extreme conditions?
      - Liquidation cascade risk?
      - Death spiral potential?

2. LP RISK SCORECARD — Score each dimension 0-5 (0=worst, 5=best) with specific evidence from code:

   | Dimension | Score | Evidence |
   |-----------|-------|----------|
   | Oracle robustness | [0-5] | [cite code: multi-source? heartbeat? fallback?] |
   | Liquidation soundness | [0-5] | [cite code: incentives? bad debt handling?] |
   | Admin privilege scope | [0-5] | [cite code: timelock? multisig? narrow powers?] |
   | Upgrade risk | [0-5] | [cite code: immutable? proxy? timelock on upgrade?] |
   | Economic design | [0-5] | [cite code: sustainable yields? Ponzi mechanics?] |
   | Governance capture resistance | [0-5] | [cite code: quorum? flash-loan protection?] |
   | Dependency risk | [0-5] | [list external protocols, failure cascade?] |
   | Exit liquidity | [0-5] | [can large LP exit with <2% slippage?] |
   | Insurance/backstop | [0-5] | [reserve fund? coverage amount?] |
   | Operational maturity | [0-5] | [monitoring? pause? incident response?] |

3. COMPARATIVE POSITIONING — How does this protocol's risk compare to:
   - Aave V3 (lending)
   - Compound V3 (lending)
   - Uniswap V4 (AMM)
   - Curve (stableswap)
   [Compare only against relevant category]

Output:

STRESS_TEST_RESULTS:
  Scenario A: [outcome]
  Scenario B: [outcome]
  Scenario C: [outcome]
  Scenario D: [outcome]
  Scenario E: [outcome]

LP_SCORECARD:
  [table as above]
  TOTAL_SCORE: [X/50]
  RISK_TIER: [A (40-50) | B (30-39) | C (20-29) | D (10-19) | F (<10)]

COMPARATIVE: [vs established protocols]

GO_NO_GO: [DEPLOY | DEPLOY_WITH_LIMITS | AVOID]
POSITION_LIMITS: [if DEPLOY_WITH_LIMITS, what limits?]
CIRCUIT_BREAKERS: [conditions under which LP should exit immediately]
  1. [condition]
  2. [condition]
  3. [condition]
```

**IMPORTANT: Both MCP tools MUST be called in the SAME message. After BOTH return, save outputs.**

### Step 3: Wait for all agents and collect

```bash
wait
echo "=== ALL 6 REVIEWERS COMPLETE ==="
echo ""
echo "=== Exploit Hunter ===" && head -20 /tmp/audit-exploits.txt
echo "=== Admin Abuse ===" && head -20 /tmp/audit-admin-abuse.txt
echo "=== Economic Risk ===" && head -20 /tmp/audit-economic.txt
echo "=== Ops Risk ===" && head -20 /tmp/audit-ops-risk.txt
echo ""
echo "Codex and Gemini outputs available from MCP calls above."
```

**Save all 6 outputs to `.claude/temp/audit-phase3-findings.md`** (concatenate with headers).

---

## Phase 4: BLUE TEAM (1 Claude + Gemini tiebreaker)

### Step 1: Claude Blue Team agent

```bash
claude -p "You are a smart contract DEFENDER. Your job: challenge every finding.
For every finding, prove it WRONG or confirm it's REAL. No handwaving — cite code.

Read:
- All .sol files (the actual code)
- .claude/temp/audit-traces.md (verified call paths)
- .claude/temp/audit-phase3-findings.md (all 6 reviewers' findings)

For EACH finding from ALL 6 reviewers:

---
FINDING: [title from red team]
SOURCE: [which reviewer: exploit-hunter|admin-abuse|econ-analyst|ops-risk|codex|gemini]
ORIGINAL_SEVERITY: [as reported]
BLUE_TEAM_STATUS: [CONFIRMED | MITIGATED | FALSE_POSITIVE | DISPUTED]
EVIDENCE:
  [If CONFIRMED: explain why the vulnerability is real, cite attack path through actual code]
  [If MITIGATED: cite EXACT code line/function that prevents exploitation]
  [If FALSE_POSITIVE: explain why the attack path does not work in practice]
  [If DISPUTED: explain the uncertainty, what additional analysis would resolve it]
ADJUSTED_SEVERITY: [same or different from original, with justification]
---

End with:

BLUE_TEAM_SUMMARY:
  TOTAL_FINDINGS_REVIEWED: [count]
  CONFIRMED: [count] (CRITICAL: [N], HIGH: [N], MEDIUM: [N], LOW: [N])
  MITIGATED: [count]
  FALSE_POSITIVE: [count]
  DISPUTED: [count]

  TOP_5_CONFIRMED_RISKS:
    1. [title] — [severity] — [one-line summary]
    2. ...
    3. ...
    4. ...
    5. ..." \
  --allowedTools Read,Glob,Grep,Bash \
  --print > /tmp/audit-blue-team.txt
```

### Step 2: Gemini tiebreaker on DISPUTED findings

**Only run if there are DISPUTED findings.**

Extract disputed findings from blue team output. Call `mcp__gemini__ask-gemini`:

```text
Working directory: [pwd]

The blue team has DISPUTED some audit findings — they couldn't confirm or deny.
You are the independent tiebreaker. Read the actual code and make a final call.

Read: all .sol files, .claude/temp/audit-traces.md

For each disputed finding below, provide your independent assessment:

[paste all DISPUTED findings from blue team]

For each:
---
FINDING: [title]
GEMINI_VERDICT: [CONFIRMED | NOT_EXPLOITABLE]
CONFIDENCE: [LOW|MEDIUM|HIGH]
REASONING: [detailed analysis with specific code references]
---
```

**Merge Gemini verdicts into blue team results. Save to `.claude/temp/audit-blue-team.md`.**

---

## Phase 5: LP RISK SCORECARD (orchestrator)

Compile from Gemini's LP scorecard (Phase 3) + all CONFIRMED findings into the final score.

```text
┌────────────────────────────────────────────────────────────┐
│ LP RISK SCORECARD                                          │
├────────────────────────────────────────────────────────────┤
│ Category                    │ Score (0-5) │ Key Finding    │
├─────────────────────────────┼─────────────┼────────────────┤
│ Smart Contract Security     │ [N]         │ [note]         │
│ Admin/Privilege Risk        │ [N]         │ [note]         │
│ Oracle Robustness           │ [N]         │ [note]         │
│ Economic Design             │ [N]         │ [note]         │
│ Liquidation Soundness       │ [N]         │ [note]         │
│ Governance Resistance       │ [N]         │ [note]         │
│ Dependency Risk             │ [N]         │ [note]         │
│ Upgrade Safety              │ [N]         │ [note]         │
│ Exit Liquidity              │ [N]         │ [note]         │
│ Operational Maturity        │ [N]         │ [note]         │
├─────────────────────────────┼─────────────┼────────────────┤
│ TOTAL                       │ [X/50]      │                │
│ RISK TIER                   │ [A-F]       │                │
│ VERDICT                     │ [GO/LIMIT/AVOID]             │
├────────────────────────────────────────────────────────────┤
│ HARD FAILS (any single one = automatic AVOID):             │
│ □ Unresolved CRITICAL finding                              │
│ □ Admin can drain without timelock                         │
│ □ Single EOA owner with upgrade rights                     │
│ □ Oracle: single source, no staleness check                │
│ □ Death spiral risk confirmed                              │
│ □ Score < 20/50                                            │
├────────────────────────────────────────────────────────────┤
│ RISK TIERS:                                                │
│   A (40-50): Low risk — deploy with standard monitoring    │
│   B (30-39): Moderate — deploy with position limits        │
│   C (20-29): Elevated — deploy only with active hedging    │
│   D (10-19): High — avoid or minimal test allocation only  │
│   F  (<10) : Critical — do not deploy                      │
└────────────────────────────────────────────────────────────┘
```

---

## Phase 6: SYNTHESIS (1 Claude agent)

```bash
claude -p "You are a report writer synthesizing a smart contract audit.

Read ALL artifacts:
- .claude/temp/audit-inventory.md (system map)
- .claude/temp/audit-traces.md (call traces)
- .claude/temp/audit-phase3-findings.md (6 reviewers' raw findings)
- .claude/temp/audit-blue-team.md (blue team validation)
- LP RISK SCORECARD data (will be provided inline)

Write a comprehensive audit report with this EXACT structure:

# Smart Contract Audit Report: [Protocol Name]
## Date: [YYYY-MM-DD]
## Methodology: AI Multi-Agent Audit (4 Claude specialists + Codex + Gemini + Blue Team)

## Executive Summary
[2-3 paragraphs: what this protocol does, overall risk level, GO/LIMIT/AVOID verdict,
and the top 3 things an LP should know before deploying capital]

## LP Risk Scorecard
[formatted scorecard table from Phase 5]

## Findings Summary
| ID | Title | Severity | Category | Status | Source |
|all CONFIRMED findings, sorted by severity|

## Critical Findings
[full detail for each CRITICAL finding: description, exploit scenario, recommendation]

## High Findings
[full detail]

## Medium Findings
[full detail]

## Low / Informational
[condensed — title + one-line description]

## Admin Trust Assumptions
[everything an LP must trust the admin NOT to do — bullet list]

## Economic Risk Assessment
[stress test results from Gemini + econ-analyst findings]

## System Architecture
[from traces — how the protocol actually works, in plain English]

## Recommendations (prioritized)
1. [most urgent — what to fix first]
2. ...
N. ...

## Circuit Breakers for LPs
[conditions under which an LP should exit their position immediately]

## Appendix A: Full Call Traces
[reference to audit-traces.md]

## Appendix B: Blue Team Assessments
[summary of confirmed vs false positive ratios per reviewer]

## Appendix C: Comparative Analysis
[how this protocol compares to established protocols]

Write output to: .claude/temp/audit-report.md" \
  --allowedTools Read,Glob,Grep,Bash,Write \
  --print
```

**VERIFY**: Show `cat .claude/temp/audit-report.md | head -60`

---

## Phase 7: HUMAN GATE

**STOP and present to user:**

### Audit Complete — Review Required

**Protocol**: [name]
**Risk Tier**: [A-F] — **Verdict**: [GO/LIMIT/AVOID]
**Score**: [X/50]

| Severity | Confirmed | False Positive |
|----------|-----------|---------------|
| CRITICAL | [N] | [N] |
| HIGH | [N] | [N] |
| MEDIUM | [N] | [N] |
| LOW/INFO | [N] | [N] |

**Top 3 Risks:**
1. [title — severity]
2. [title — severity]
3. [title — severity]

**Hard Fails**: [any triggered? which?]

Full report: `.claude/temp/audit-report.md`

**Awaiting user approval to finalize...**

---

## Phase 8: DELIVERABLE

After user approval:

```bash
# Create audits directory if needed
mkdir -p audits

# Determine protocol name
PROTOCOL_NAME=$(head -3 .claude/temp/audit-report.md | grep -oP '(?<=: ).*' | head -1 | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
DATE=$(date +%Y-%m-%d)
REPORT_FILE="audits/${PROTOCOL_NAME}-audit-${DATE}.md"

# Copy report to deliverable location
cp .claude/temp/audit-report.md "$REPORT_FILE"

echo "Audit report written to: $REPORT_FILE"
ls -la "$REPORT_FILE"
```

**Final output:**

```text
┌─────────────────────────────────────────────────────────┐
│ SC-AUDIT COMPLETE                                       │
├─────────────────────────────────────────────────────────┤
│ Protocol: [name]                                        │
│ Risk Tier: [A-F]                                        │
│ Score: [X/50]                                           │
│ Verdict: [GO|LIMIT|AVOID]                               │
│ Confirmed Findings: [N] (C:[n] H:[n] M:[n] L:[n])      │
│ False Positives Caught: [N]                             │
│ Reviewers: 4 Claude + Codex + Gemini + Blue Team        │
│ Report: [path to file]                                  │
│ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]                        │
└─────────────────────────────────────────────────────────┘
```

---

## Circuit Breakers

| Trigger | Action |
|---------|--------|
| No .sol files found | STOP: "No Solidity contracts found" |
| Inventory failed | STOP: Cannot proceed without system map |
| Trace agent exceeded context | Split contracts, trace in batches |
| Any reviewer returns empty output | Re-run that reviewer |
| Blue team cannot access findings | STOP: Verify Phase 3 outputs exist |
| All 6 reviewers found 0 findings | Flag as suspicious — re-run with broader scope |
| >50 total findings | Prioritize CRITICAL/HIGH only for blue team |

---

## Artifacts Generated

```text
.claude/temp/
├── audit-inventory.md          # Phase 1: system map
├── audit-traces.md             # Phase 2: call traces + invariants
├── audit-phase3-findings.md    # Phase 3: all 6 reviewers' raw findings
├── audit-blue-team.md          # Phase 4: confirmed/rebutted findings
└── audit-report.md             # Phase 6: final synthesized report

audits/
└── <protocol>-audit-YYYY-MM-DD.md  # Phase 8: deliverable
```

---

## Agent Summary

| Phase | Agent | Type | Tools | Parallel? |
|-------|-------|------|-------|-----------|
| 1 | orchestrator | main context | Read, Glob, Grep | — |
| 2 | tracer | `claude -p` subprocess | Read, Glob, Grep, Bash | sequential |
| 3 | exploit-hunter | `claude -p` subprocess | Read, Glob, Grep, Bash | **parallel** |
| 3 | admin-abuse-hunter | `claude -p` subprocess | Read, Glob, Grep, Bash | **parallel** |
| 3 | econ-analyst | `claude -p` subprocess | Read, Glob, Grep, Bash | **parallel** |
| 3 | ops-risk-analyst | `claude -p` subprocess | Read, Glob, Grep, Bash | **parallel** |
| 3 | Codex | `mcp__codex-cli__codex` | — | **parallel** |
| 3 | Gemini | `mcp__gemini__ask-gemini` | — | **parallel** |
| 4 | blue-team | `claude -p` subprocess | Read, Glob, Grep, Bash | sequential |
| 4 | Gemini tiebreaker | `mcp__gemini__ask-gemini` | — | conditional |
| 6 | synthesizer | `claude -p` subprocess | Read, Glob, Grep, Bash, Write | sequential |

**Total: 8 Claude + 2 Codex + 3 Gemini = 13 agent calls**

---

## User's Task

$ARGUMENTS
