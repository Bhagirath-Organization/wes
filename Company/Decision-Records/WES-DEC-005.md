# WES-DEC-005 — Ratification of the Phase-1 SOP Library (SOPs 05–10)

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-005 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved (Ratified) |

## Decision Summary
The Founder ratifies the **Phase-1 SOP Library** — `SOP-CODING` (05), `SOP-REVIEW` (06),
`SOP-TESTING` (07), `SOP-DEPLOYMENT` (08), `SOP-DOCUMENTATION` (09), and `SOP-SECURITY` (10),
all v1.0 — as the operative Standard Operating Procedures governing engineering work in WES.

## Reason
- The six SOPs are the procedure layer beneath the Constitution; every AI Engineer needs
  ratified (not draft) procedures to work against.
- The Founder declared **"merge = Batch-2 ratification"** on the Batch-2 PR (#4) merge; this
  record makes that ratification explicit in the repository.

## Alternatives Considered
- **Leave the SOPs as Draft.** Rejected — AI Employees must follow ratified procedures.
- **Ratify in a standalone PR.** Rejected — the Founder directed that this ratification be the
  **first commit of the Batch-3 branch** (mirroring WES-DEC-003), not a separate PR.

## Final Decision
`SOP-CODING`, `SOP-REVIEW`, `SOP-TESTING`, `SOP-DEPLOYMENT`, `SOP-DOCUMENTATION`, and
`SOP-SECURITY` (docs 05–10, v1.0) are **Ratified**, effective 2026-08-04. Batch-2 was merged to
`main` via **PR #4** (squash `714fdf5`). The `INVENTORY` is updated to mark docs 05–10 **Ratified**.

## Impact
- The six SOPs are now the authoritative engineering procedures, cited by every subsequent
  document (including the Batch-3 role prompts).
- A future change to any ratified SOP requires a new version and a new `WES-DEC-###`
  (SOP-DOCUMENTATION §7).
- No code, no deployment — production remains held for the combined end-of-phase deploy.

## References
- `Company/Operating-Instructions/SOP-CODING.md`, `SOP-REVIEW.md`, `SOP-TESTING.md`,
  `SOP-DEPLOYMENT.md`, `SOP-DOCUMENTATION.md`, `SOP-SECURITY.md`
- `Company/Operating-Instructions/INVENTORY.md`
- Related: [[WES-DEC-003]], [[WES-DEC-004]]
