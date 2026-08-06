# WES-DEC-008 — Ratification of the shared activity prompts (docs 24–26)

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-008 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved (Ratified) |

## Decision Summary
The Founder ratifies the three **shared activity prompts** — `PROMPT-TASK` (doc 24), `PROMPT-REVIEW`
(doc 25), and `PROMPT-ESC` (doc 26), all v1.0 — the WES Prompt Library `TASK` / `REVIEW` /
`ESCALATION` templates injected at runtime alongside `PROMPT-SYS-CORE` and a Role Prompt.

## Reason
- These are the activity layer every AI Employee uses to execute, review, and escalate; AI Employees
  require ratified (not draft) activity prompts.
- The Founder declared **"merge = Batch-4 ratification"** on the Batch-4 PR (#7) merge; this record
  makes that ratification explicit in the repository.

## Alternatives Considered
- **Leave them as Draft.** Rejected — AI Employees must follow ratified activity prompts.
- **Ratify in a standalone PR.** Rejected — the Founder directed that this ratification be the
  **first commit of the Batch-5 branch** (mirroring WES-DEC-003 / 005 / 007).

## Final Decision
Shared activity prompts **24–26 (v1.0)** are **Ratified**, effective 2026-08-04. Batch-4 was merged to
`main` via **PR #7** (squash `2322fbe`). The `INVENTORY` is updated to mark docs 24–26 **Ratified**.

## Impact
- The full Operating Instructions **prompt stack** is now ratified: `PROMPT-SYS` (Constitution) +
  `PROMPT-SYS-CORE` + the 13 role prompts + the three activity prompts.
- Only **doc 27 (`TEST-MISSION-CHARTER`)** remains — the live end-to-end test, after which the single
  combined production deploy question goes to the Founder.
- **Carried phase-end items:** the three-role RBAC watch trio (QA `quality:review`, DevOps
  `devops:execute`, Technical Writer `knowledge:write`) and the `seed_ai.py` naming mismatch — both
  to be observed in the doc-27 live test.
- No code, no deployment — production remains held.

## References
- `Company/Operating-Instructions/PROMPT-TASK.md`, `PROMPT-REVIEW.md`, `PROMPT-ESC.md`; `INVENTORY.md`
- Related: [[WES-DEC-005]], [[WES-DEC-007]]
