# Reviewing shared reflections with judgment

Updated: 27-oct-2026.

A normal request such as “Review the reflections from all four agents and propose improvements to global AGENTS.md; do not edit it yet” is sufficient. Special review/apply commands and JSON files are not required. Existing CLI helpers can help enumerate records, check stale inputs and preserve backups; they do not decide which lessons deserve a rule.

Read the current global instructions, then the incident evidence in every machine/agent folder under `global/log/`, including older machine labels. Account for host Codex, host Claude, VM Codex and VM Claude; distinguish empty, missing and unreadable sources. Shared records are evidence of incidents, not proof of live machine configuration.

New project reflections update the project's instruction file during authorized work and write the detailed incident once into that machine/agent's central reflection folder. The record names its project. A useful global proposal may be included, but recording never changes global rules. Cross-project incidents use the same central agent folder without editing an arbitrary project.

Legacy project-only logs are preserved in their projects and are not automatically migrated. Do not claim a central review covers that older history. Read known project logs when relevant and within the user's requested scope; do not silently scan unrelated projects.

For each possible lesson, use judgment:

- Establish actual versus expected behavior, evidence, cause, immediate correction and whether prevention has actually been exercised. An assertion in a log is not automatically a fact.
- Group incidents by their real cause, not just an exact key, repeated wording or frustration. Preserve distinct incidents and source references; do not count repeated discussion as a new failure.
- Decide whether the lesson belongs in code/tests, a project rule, a skill, or global instructions. A single incident can justify a clear general lesson; repetition alone does not prove that a global rule helps.
- Check whether an existing rule already covers it. Prefer refining a precise rule over adding another overlapping instruction. Explain contradictions and cases where no rule change is warranted.
- Keep global rules concise and within their existing budget. Keep incident stories and history in the logs. Never add automatic punishments or halts because a count increased.

Present the few changes worth making, their source incidents, reasons and exact proposed diff. Do not mechanically append every proposal, rewrite the whole rules file, or treat a helper's ready-to-apply flag as approval.

A request to review means read-only. Only after the user explicitly approves the proposed global changes may an agent apply them. Re-read the file before applying, preserve a recovery copy, apply only the approved changes and retain unrelated rules. If the approved diff is stale, show the changed proposal instead of silently expanding the approval. Do not commit, push, delete history or rewire links unless separately instructed.

The shared-root constraint is: “keep all code, data and intermediates inside the user-designated shared root.” Host access is established at `/Users/elpinguino/VM-shared`; this guide does not establish current VM access. Keep authorized review artifacts and recovery copies in the shared checkout. Ordinary recording/review never changes file-access permissions.
