# WES-DEC-001 — Ratification of the AI Employee Constitution (PROMPT-SYS v1.1 & PROMPT-SYS-CORE v1.0)

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-001 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved (Ratified) |

## Decision Summary
The Founder ratifies the **Master System Prompt `PROMPT-SYS` v1.1** (the Constitution of AI
Employees) and its distilled injection **`PROMPT-SYS-CORE` v1.0** as the operative,
highest-authority instructions delivered to every AI Employee before its Role Prompt.

## Reason
- The Constitution is grounded end-to-end in the Blueprint (Vol 01–10) and the Company
  operating systems; a constitutional freeze review confirmed no duplicated authority or
  governance, no contradictions, and full Blueprint alignment.
- `PROMPT-SYS-CORE` v1.0 is a faithful, per-execution distillation that adds no new law; its
  one numeric-threshold deviation was reconciled to match Constitution §15.
- The company requires a stable, multi-year constitutional baseline before further Operating
  Instructions documents build on it.

## Alternatives Considered
- **Leave PROMPT-SYS unratified (Committee-adopted only).** Rejected — downstream documents
  and the seeded `PROMPT-SYS` template need a ratified baseline.
- **Embed Founder Intent / Company Philosophy in the Constitution.** Rejected — kept as external
  governed documents (Constitution §12) so strategy can evolve without amending the Constitution.
- **Keep the drafted "same failure repeats three times" trigger.** Rejected — softened to a
  qualitative trigger to comply with §15 ("Numeric escalation thresholds are Not defined").

## Final Decision
`PROMPT-SYS` **v1.1** and `PROMPT-SYS-CORE` **v1.0** are **Ratified**, effective 2026-08-04.
`PROMPT-SYS.md` §23 (Approval Status) and the `INVENTORY` are updated to reflect ratification.

## Impact
- Governed home: `Company/Operating-Instructions/PROMPT-SYS.md` (full Constitution) and
  `Company/Operating-Instructions/PROMPT-SYS-CORE.md` (distilled injection).
- The `PROMPT-SYS` PromptTemplate is seeded at **version 2** with the distilled content
  (merged to `main` via PR #1, `9945792`).
- **Deployment is held** for the combined final deploy after the Operating Instructions phase;
  on that deploy `sync_prompt_sys()` updates the live `PROMPT-SYS` row to v2 in place.

## References
- `Company/Operating-Instructions/PROMPT-SYS.md` (v1.1, Ratified)
- `Company/Operating-Instructions/PROMPT-SYS-CORE.md` (v1.0)
- `Company/Operating-Instructions/INVENTORY.md`
- Related: [[WES-DEC-002]]
