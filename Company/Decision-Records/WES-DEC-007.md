# WES-DEC-007 — Ratification of the Role Prompt Library (role prompts 11–23)

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-007 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved (Ratified) |

## Decision Summary
The Founder ratifies the **Role Prompt Library** — the 13 AI-employee role prompts (docs 11–23),
all v1.0: `ROLE-STUDIO-DIRECTOR`, `ROLE-PRODUCT-MANAGER`, `ROLE-UX-UI-DESIGNER`,
`ROLE-SOFTWARE-ARCHITECT`, `ROLE-FRONTEND-ENGINEER`, `ROLE-BACKEND-ENGINEER`, `ROLE-AI-ENGINEER`,
`ROLE-PROMPT-ENGINEER`, `ROLE-QA-ENGINEER`, `ROLE-SECURITY-ENGINEER`, `ROLE-PROJECT-MANAGER`,
`ROLE-DEVOPS-AUTOMATION-ENGINEER`, `ROLE-TECHNICAL-WRITER`.

## Reason
- Each role prompt is the per-employee operating layer injected after `PROMPT-SYS` and alongside
  `PROMPT-SYS-CORE`; AI Employees require ratified (not draft) role prompts to operate.
- The Founder declared **"merge = Batch-3 ratification"** on the Batch-3 PR (#6) merge; this record
  makes that ratification explicit in the repository.

## Alternatives Considered
- **Leave the role prompts as Draft.** Rejected — AI Employees must follow ratified role prompts.
- **Ratify in a standalone PR.** Rejected — the Founder directed that this ratification be the
  **first commit of the Batch-4 branch** (mirroring WES-DEC-003 and WES-DEC-005), not a separate PR.

## Final Decision
Role prompts **11–23 (v1.0)** are **Ratified**, effective 2026-08-04. Batch-3 was merged to `main`
via **PR #6** (squash `65681cf`). The `INVENTORY` is updated to mark docs 11–23 **Ratified**.

## Impact
- The 13 role prompts are now the authoritative per-role operating instructions.
- **Carried phase-end reconciliation items (not resolved here):** the three-role RBAC watch trio —
  QA (`quality:review`), DevOps (`devops:execute`), Technical Writer (`knowledge:write`) — each with a
  core duty mapping to a Lead/Director permission not held as Operational (`EMPLOYEE`); and the
  `seed_ai.py` naming mismatch. Both to be observed in the doc-27 live test.
- No code, no deployment — production remains held for the combined end-of-phase deploy.

## References
- `Company/Operating-Instructions/ROLE-*.md` (docs 11–23); `Company/Operating-Instructions/INVENTORY.md`
- Related: [[WES-DEC-005]], [[WES-DEC-006]]
