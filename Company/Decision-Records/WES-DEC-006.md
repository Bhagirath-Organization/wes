# WES-DEC-006 — AI-employee authority level → platform RBAC role mapping

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-006 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved |

## Decision Summary
The Founder confirms the mapping from an AI employee's **authority level** to its **platform
RBAC role** (`app/domain/roles.py`):

| Authority level | RBAC role | Example employees |
|---|---|---|
| **Executive** | `DIRECTOR` | Studio Director |
| **Lead** | `DEPARTMENT_HEAD` | Product Manager, Software Architect, Project Manager |
| **Operational** | `EMPLOYEE` (read-only) | UX/UI Designer, Frontend/Backend/AI/Prompt Engineers, QA, Security, DevOps, Technical Writer |

The human **Founder / Owner** is separate (RBAC role `FOUNDER`, full access).

## Reason
- Role prompts (docs 11–23) must state authority that is **RBAC-verified**, not inferred; this
  record makes the mapping authoritative so each role prompt can cite it.
- The three AI authority levels (Executive / Lead / Operational) already exist in the org; this
  binds each to the enforced permission set in code.

## Alternatives Considered
- **Leave the mapping inferred per role prompt.** Rejected — authority claims must be grounded.
- **Codify the mapping in code now.** Deferred — this Decision Record is the authoritative mapping;
  codifying it in `app/domain/roles.py` (or an AI-employee → Role table) is an optional future
  engineering task, not required for the role prompts.

## Final Decision
The Executive→`DIRECTOR` / Lead→`DEPARTMENT_HEAD` / Operational→`EMPLOYEE` mapping is **confirmed**,
effective 2026-08-04. Each role prompt states the employee's authority as the permission set of its
mapped `Role` in `app/domain/roles.py`. **`EMPLOYEE` is read-only**; Operational employees produce
work through assigned tasks and the gated workflow, not through personal write permissions.

## Impact
- Role prompts cite authority as **"confirmed (WES-DEC-006)"**; `ROLE-PRODUCT-MANAGER` (doc 12)
  Open Founder Decision is resolved.
- The separate `seed_ai.py` **naming** mismatch (divergent AI-org role names) remains an open
  phase-end item — it is not resolved by this record.
- No code, no deployment.

## References
- `app/domain/roles.py` (`Role`, `ROLE_PERMISSIONS`)
- `Company/Operating-Instructions/` role prompts (docs 11–23); `INVENTORY.md`
- Related: [[WES-DEC-005]]
