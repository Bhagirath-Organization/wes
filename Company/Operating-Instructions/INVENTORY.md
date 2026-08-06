# WES Operating Instructions — INVENTORY (living register)

| Field | Detail |
|-------|--------|
| **Program** | WES Operating Instructions Program (27 documents) |
| **Owner** | WES Constitutional Committee / Founder (Human) |
| **Register status** | Active — updated per document |
| **Last updated** | 2026-08-04 |

---

## ⚠️ Deploy policy (binding for this phase)

> **All Operating Instructions changes are merged to `main` but NOT deployed individually.**
> There will be **one combined final deploy** to production (green / VPS) **after the entire
> Operating Instructions phase is complete**. Merges may proceed (Founder-approved); production
> is held until the batched final deploy.

**Consequence:** merged code (e.g. PROMPT-SYS v2 seed) is on `main` but **not live**. On the
final deploy, `seed_execution()` → `sync_prompt_sys()` will update `PROMPT-SYS` to v2 in place
on the production database. No live database has been touched.

---

## Documents

| # | Doc ID | Title | Version | Status | Repo location |
|---|--------|-------|---------|--------|---------------|
| 01 | `PROMPT-SYS` | Master System Prompt (Constitution) | 1.1 | **Ratified** (`WES-DEC-001`, 2026-08-04) | `Company/Operating-Instructions/PROMPT-SYS.md` |
| 02 | `PROMPT-SYS-CORE` | Distilled Injection Version | 1.0 | **Ratified** (`WES-DEC-001`, 2026-08-04) | `Company/Operating-Instructions/PROMPT-SYS-CORE.md` |
| 03 | `FOUNDER-INTENT` | Founder Intent (governed, §12) | 1.0 | **Ratified** (`WES-DEC-003`, 2026-08-04) | `Company/Operating-Instructions/FOUNDER-INTENT.md` |
| 04 | `COMPANY-PHILOSOPHY` | Company Philosophy (governed, §12) | 1.0 | **Ratified** (`WES-DEC-003`, 2026-08-04) | `Company/Operating-Instructions/COMPANY-PHILOSOPHY.md` |
| 05 | `SOP-CODING` | Coding SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-CODING.md` |
| 06 | `SOP-REVIEW` | Review SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-REVIEW.md` |
| 07 | `SOP-TESTING` | Testing SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-TESTING.md` |
| 08 | `SOP-DEPLOYMENT` | Deployment SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-DEPLOYMENT.md` |
| 09 | `SOP-DOCUMENTATION` | Documentation SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-DOCUMENTATION.md` |
| 10 | `SOP-SECURITY` | Security SOP (Phase 1 — SOP Library) | 1.0 | **Ratified** (`WES-DEC-005`, 2026-08-04) | `Company/Operating-Instructions/SOP-SECURITY.md` |
| 11 | `ROLE-STUDIO-DIRECTOR` | Role Prompt — Studio Director (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-STUDIO-DIRECTOR.md` |
| 12 | `ROLE-PRODUCT-MANAGER` | Role Prompt — Product Manager (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-PRODUCT-MANAGER.md` |
| 13 | `ROLE-UX-UI-DESIGNER` | Role Prompt — UX/UI Designer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-UX-UI-DESIGNER.md` |
| 14 | `ROLE-SOFTWARE-ARCHITECT` | Role Prompt — Software Architect (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-SOFTWARE-ARCHITECT.md` |
| 15 | `ROLE-FRONTEND-ENGINEER` | Role Prompt — Frontend Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-FRONTEND-ENGINEER.md` |
| 16 | `ROLE-BACKEND-ENGINEER` | Role Prompt — Backend Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-BACKEND-ENGINEER.md` |
| 17 | `ROLE-AI-ENGINEER` | Role Prompt — AI Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-AI-ENGINEER.md` |
| 18 | `ROLE-PROMPT-ENGINEER` | Role Prompt — Prompt Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-PROMPT-ENGINEER.md` |
| 19 | `ROLE-QA-ENGINEER` | Role Prompt — QA Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-QA-ENGINEER.md` |
| 20 | `ROLE-SECURITY-ENGINEER` | Role Prompt — Security Engineer (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-SECURITY-ENGINEER.md` |
| 21 | `ROLE-PROJECT-MANAGER` | Role Prompt — Project Manager (Batch-3) | 1.0 | **Draft** (batch-3) | `Company/Operating-Instructions/ROLE-PROJECT-MANAGER.md` |
| 22–27 | — | (pending) | — | Not started | — |

## Decision Records

| ID | Summary | Date | Location |
|----|---------|------|----------|
| `WES-DEC-001` | Ratification of PROMPT-SYS v1.1 & PROMPT-SYS-CORE v1.0 by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-001.md` |
| `WES-DEC-002` | Agent may create PRs and execute Founder-instructed merges via the GitHub App; merge decision stays Founder-only | 2026-08-04 | `Company/Decision-Records/WES-DEC-002.md` |
| `WES-DEC-003` | Ratification of FOUNDER-INTENT v1.0 & COMPANY-PHILOSOPHY v1.0 by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-003.md` |
| `WES-DEC-004` | Ratcheting backend test-coverage floor — baseline 73%, floor 71% | 2026-08-04 | `Company/Decision-Records/WES-DEC-004.md` |
| `WES-DEC-005` | Ratification of the Phase-1 SOP Library (SOPs 05–10) by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-005.md` |
| `WES-DEC-006` | AI-employee authority → RBAC role mapping (Executive→DIRECTOR, Lead→DEPARTMENT_HEAD, Operational→EMPLOYEE) | 2026-08-04 | `Company/Decision-Records/WES-DEC-006.md` |

## Code / integration changes

| Change | PR | Merge | Deployed? |
|--------|----|-------|-----------|
| Seed `PROMPT-SYS` v2 (PROMPT-SYS-CORE) + idempotent `sync_prompt_sys()` in-place upsert | **#1** | **Merged (squash)** `9945792` on 2026-08-04 | **NO — held for combined final deploy** |
| Batch-0 close: ratified `PROMPT-SYS.md`, `WES-DEC-001/002`, INVENTORY | **#2** | **Merged (squash)** `99de3f9` on 2026-08-04 | **NO — docs only, no deploy** |
| Batch-1 (strategy): `FOUNDER-INTENT` + `COMPANY-PHILOSOPHY` (docs 03–04) | **#3** | **Merged (squash)** `43bb56b` on 2026-08-04 | **NO — docs only, no deploy** |
| Batch-2 (SOPs): `WES-DEC-003` + SOPs 05–10 | **#4** | **Merged (squash)** `714fdf5` on 2026-08-04 | **NO — docs only, no deploy** |
| CI coverage enforcement (WES-DEC-004): `pytest-cov` + `scripts/test.sh --cov-fail-under=71` | **#5** | **Merged (squash)** `0f661a8` on 2026-08-04 | **NO — CI tooling; no deploy** |

## Verification log

- **PROMPT-SYS-CORE / seed v2** — isolated throwaway-DB check **12/12 pass** (fresh insert v2,
  in-place update from old v1 stub, idempotent no-op, insert-if-missing); injection = **642 words**.
- **Full backend suite** (keyless sandbox, in-memory SQLite): **461 collected → 460 passed, 1 failed.**
  The one failure — `test_autonomous_engineering_atlas.py::test_execute_dry_run_is_side_effect_free`
  — is **environment-only** (`GitHubService.configured()` false without the App key) and **unrelated
  to this change**. Note: this checkout's backend suite is **461** tests (not the earlier "922" figure).

## Pending actions — for the combined FINAL deploy (end of phase)

1. Deploy merged `main` to green (production) — **Founder-gated**, held until phase end.
2. On deploy, confirm `PROMPT-SYS` **v2** appears in the live `/execution` Prompt Library
   (`sync_prompt_sys()` updates it in place; no destructive re-seed).

## Open items

- Pre-existing **ATLAS Sprint 02/03** work remains uncommitted in the `/opt/wes-green` working tree
  (separate from this program; intentionally not touched by these branches).
- **CI coverage enforcement (WES-DEC-004)** — **done**: `pytest-cov` added to `backend/requirements.txt`
  and `scripts/test.sh` wired with `--cov=app --cov-fail-under=71`. Delivered as the docs phase's
  **first code change, following `SOP-CODING` end-to-end** (branch `feature/coverage-ci-enforcement`;
  **PR #5 merged** `0f661a8`).
- **Frontend coverage floor** — deferred (WES-DEC-004); set by ratchet after the frontend suite
  matures (revisit at the end of the Operating Instructions phase).
- **Watch (doc 27 live test):** Operational roles map to `EMPLOYEE` = **read-only** (WES-DEC-006).
  Observe in the doc 27 live end-to-end test (`TEST-MISSION-CHARTER`) whether this creates runtime
  friction — i.e. whether Operational employees' work flows cleanly through the gated workflow, or
  whether the read-only constraint needs a codified exception. Record the observation as a Founder
  decision at phase end.
- **Code vs canonical role naming — phase-end reconciliation (Founder decision).**
  `backend/app/db/seed_ai.py` seeds a divergent AI-org model (roles `CEO` / `CTO` / `Chief
  Architect`, 12 employees, no Prompt Engineer / Project Manager) that does **not** match the
  canonical 13-role org (Studio Director, …) in `Employees/`, Blueprint Vol 03, and `Company/`.
  The Batch-3 role prompts anchor on the **canonical org + the platform RBAC** (`app/domain/roles.py`),
  never on `seed_ai.py`. Reconcile at phase end: realign the code seed to the canonical org, or
  record a Founder decision to accept the divergence. (The AI-employee → platform-RBAC-role mapping
  is now **confirmed by WES-DEC-006** — Executive→`DIRECTOR`, Lead→`DEPARTMENT_HEAD`,
  Operational→`EMPLOYEE`; codifying it in code remains an optional future engineering task.)

## Change history

| Date | Entry |
|------|-------|
| 2026-08-04 | Doc 01 `PROMPT-SYS` v1.1 authored (constitutional freeze review). Doc 02 `PROMPT-SYS-CORE` v1.0 authored, seeded as `PROMPT-SYS` v2, verified, **PR #1 merged to `main`** (`9945792`). Deploy **held** for combined final deploy. |
| 2026-08-04 | **Batch-0 close:** Founder **ratified** PROMPT-SYS v1.1 + CORE v1.0 (`WES-DEC-001`); agent PR/merge authority recorded (`WES-DEC-002`); ratified `PROMPT-SYS.md` committed; docs 01–02 marked **Ratified**. **PR #2 merged to `main`** (`99de3f9`). |
| 2026-08-04 | **Batch-1 (strategy):** committed governed docs 03 `FOUNDER-INTENT` v1.0 and 04 `COMPANY-PHILOSOPHY` v1.0 (Founder-authored, committed verbatim). **PR #3 merged to `main`** (`43bb56b`). |
| 2026-08-04 | **Batch-2 (SOPs) — WES-DEC-003:** Founder **ratified** FOUNDER-INTENT v1.0 + COMPANY-PHILOSOPHY v1.0; docs 03–04 marked **Ratified**. Bundled as the first commit on branch `docs/batch-2-sops` (PR opens after all Batch-2 SOPs land). Deploy held. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 05 `SOP-CODING` v1.0 committed (Draft) on `docs/batch-2-sops`. PR opens after all 6 Batch-2 SOPs land. Deploy held. |
| 2026-08-04 | **Batch-2 — WES-DEC-004:** measured backend coverage baseline **73%**; set ratchet floor **71%**. Frontend threshold **deferred** (ratchet after the suite matures). CI enforcement **approved as a separate engineering PR after the Batch-2 merge — must follow SOP-CODING as its first real execution**. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 06 `SOP-REVIEW` v1.0 committed (Draft) on `docs/batch-2-sops`. Deploy held. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 07 `SOP-TESTING` v1.0 committed (Draft) on `docs/batch-2-sops`. Deploy held. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 08 `SOP-DEPLOYMENT` v1.0 committed (Draft) on `docs/batch-2-sops`. Deploy held. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 09 `SOP-DOCUMENTATION` v1.0 committed (Draft) on `docs/batch-2-sops`. Deploy held. |
| 2026-08-04 | **Batch-2 (SOPs):** doc 10 `SOP-SECURITY` v1.0 committed (Draft) — Phase-1 SOP Library complete (docs 05–10). Single Batch-2 PR opened (base `main` ← `docs/batch-2-sops`). Deploy held. |
| 2026-08-04 | **Batch-2 merged:** **PR #4 merged** to `main` (`714fdf5`) — Founder declared "merge = Batch-2 ratification"; WES-DEC-005 (flip docs 05–10 → Ratified) to bundle into Batch-3. Deploy held. |
| 2026-08-04 | **Coverage CI enforcement (WES-DEC-004):** first code change of the phase — `pytest-cov` + `scripts/test.sh --cov=app --cov-fail-under=71`; followed `SOP-CODING` end-to-end (its first live execution). **PR #5 merged to `main`** (`0f661a8`). Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts) — WES-DEC-005:** Founder **ratified** the Phase-1 SOP Library (SOPs 05–10); docs 05–10 marked **Ratified**. First commit of branch `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 11 `ROLE-STUDIO-DIRECTOR` v1.0 committed (Draft) on `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 12 `ROLE-PRODUCT-MANAGER` v1.0 committed (Draft) on `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 — WES-DEC-006:** Founder **confirmed** the AI-employee authority → RBAC mapping (Executive→DIRECTOR, Lead→DEPARTMENT_HEAD, Operational→EMPLOYEE). Doc 12 Open Founder Decision resolved; docs 13–23 cite "confirmed (WES-DEC-006)". Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 13 `ROLE-UX-UI-DESIGNER` v1.0 committed (Draft) on `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 14 `ROLE-SOFTWARE-ARCHITECT` v1.0 committed (Draft) — "final approval" reconciled to the architecture-gate verdict (SOP-REVIEW); PR merge stays Founder-only. Added phase-end watch item: Operational=read-only runtime friction, observe in the doc 27 live test. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 15 `ROLE-FRONTEND-ENGINEER` v1.0 committed (Draft) on `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 16 `ROLE-BACKEND-ENGINEER` v1.0 committed (Draft) on `docs/batch-3-role-prompts`. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 17 `ROLE-AI-ENGINEER` v1.0 committed (Draft) — AI Engineer→Prompt Engineer "directs" verified (Org-Chart/Reporting-Hierarchy) and framed honestly as an org reporting line with no RBAC backing (both `EMPLOYEE`/read-only). Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 18 `ROLE-PROMPT-ENGINEER` v1.0 committed (Draft) — reporting-line framing mirrored from doc 17; governed-prompt boundary explicit (PE drafts; Prompt Library write = exec:write Lead/Director; ratification/activation Founder-only; no silent edits). Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 19 `ROLE-QA-ENGINEER` v1.0 committed (Draft) — sign-off = quality-gate review verdict (not merge/release); Director-reporting independence explicit; `quality:review` Director-level RBAC framed honestly (not held by Operational QA). Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 20 `ROLE-SECURITY-ENGINEER` v1.0 committed (Draft) — clearance/waiver in verdict-pattern (decision Security Engineer's, execution gated); first-person incident path (stop→contain→escalate→record); reviewer-vs-fixer separation explicit. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 21 `ROLE-PROJECT-MANAGER` v1.0 committed (Draft) — Product-Manager (what/why) vs Project-Manager (how/when) boundary sharp; scope authority explicitly zero (escalate, never cut); Technical-Writer direction as org line; one-line Studio-Director distinction. Deploy held. |
