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
| 11 | `ROLE-STUDIO-DIRECTOR` | Role Prompt — Studio Director (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-STUDIO-DIRECTOR.md` |
| 12 | `ROLE-PRODUCT-MANAGER` | Role Prompt — Product Manager (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-PRODUCT-MANAGER.md` |
| 13 | `ROLE-UX-UI-DESIGNER` | Role Prompt — UX/UI Designer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-UX-UI-DESIGNER.md` |
| 14 | `ROLE-SOFTWARE-ARCHITECT` | Role Prompt — Software Architect (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-SOFTWARE-ARCHITECT.md` |
| 15 | `ROLE-FRONTEND-ENGINEER` | Role Prompt — Frontend Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-FRONTEND-ENGINEER.md` |
| 16 | `ROLE-BACKEND-ENGINEER` | Role Prompt — Backend Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-BACKEND-ENGINEER.md` |
| 17 | `ROLE-AI-ENGINEER` | Role Prompt — AI Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-AI-ENGINEER.md` |
| 18 | `ROLE-PROMPT-ENGINEER` | Role Prompt — Prompt Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-PROMPT-ENGINEER.md` |
| 19 | `ROLE-QA-ENGINEER` | Role Prompt — QA Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-QA-ENGINEER.md` |
| 20 | `ROLE-SECURITY-ENGINEER` | Role Prompt — Security Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-SECURITY-ENGINEER.md` |
| 21 | `ROLE-PROJECT-MANAGER` | Role Prompt — Project Manager (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-PROJECT-MANAGER.md` |
| 22 | `ROLE-DEVOPS-AUTOMATION-ENGINEER` | Role Prompt — DevOps / Automation Engineer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-DEVOPS-AUTOMATION-ENGINEER.md` |
| 23 | `ROLE-TECHNICAL-WRITER` | Role Prompt — Technical Writer (Batch-3) | 1.0 | **Ratified** (`WES-DEC-007`, 2026-08-04) | `Company/Operating-Instructions/ROLE-TECHNICAL-WRITER.md` |
| 24 | `PROMPT-TASK` | Task Execution Prompt (Batch-4 shared) | 1.0 | **Ratified** (`WES-DEC-008`, 2026-08-04) | `Company/Operating-Instructions/PROMPT-TASK.md` |
| 25 | `PROMPT-REVIEW` | Review Prompt (Batch-4 shared) | 1.0 | **Ratified** (`WES-DEC-008`, 2026-08-04) | `Company/Operating-Instructions/PROMPT-REVIEW.md` |
| 26 | `PROMPT-ESC` | Escalation Prompt (Batch-4 shared) | 1.0 | **Ratified** (`WES-DEC-008`, 2026-08-04) | `Company/Operating-Instructions/PROMPT-ESC.md` |
| 27 | `TEST-MISSION-CHARTER` | First Live End-to-End Mission (Batch-5) | 1.0 | **Ratified** (`WES-DEC-010`, 2026-08-08) | `Company/Operating-Instructions/TEST-MISSION-CHARTER.md` |

## Decision Records

| ID | Summary | Date | Location |
|----|---------|------|----------|
| `WES-DEC-001` | Ratification of PROMPT-SYS v1.1 & PROMPT-SYS-CORE v1.0 by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-001.md` |
| `WES-DEC-002` | Agent may create PRs and execute Founder-instructed merges via the GitHub App; merge decision stays Founder-only | 2026-08-04 | `Company/Decision-Records/WES-DEC-002.md` |
| `WES-DEC-003` | Ratification of FOUNDER-INTENT v1.0 & COMPANY-PHILOSOPHY v1.0 by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-003.md` |
| `WES-DEC-004` | Ratcheting backend test-coverage floor — baseline 73%, floor 71% | 2026-08-04 | `Company/Decision-Records/WES-DEC-004.md` |
| `WES-DEC-005` | Ratification of the Phase-1 SOP Library (SOPs 05–10) by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-005.md` |
| `WES-DEC-006` | AI-employee authority → RBAC role mapping (Executive→DIRECTOR, Lead→DEPARTMENT_HEAD, Operational→EMPLOYEE) | 2026-08-04 | `Company/Decision-Records/WES-DEC-006.md` |
| `WES-DEC-007` | Ratification of the Role Prompt Library (role prompts 11–23) by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-007.md` |
| `WES-DEC-008` | Ratification of the shared activity prompts (PROMPT-TASK/REVIEW/ESC, docs 24–26) by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-008.md` |
| `WES-DEC-009` | Mission budget enforcement: per-run $5 + hard_stop supersedes charter "all limits $5" (pre-existing live usage) | 2026-08-07 | `Company/Decision-Records/WES-DEC-009.md` |
| `WES-DEC-010` | TEST-MISSION-01 outcome accepted; doc 27 ratification recorded; reconciliation roadmap ratified | 2026-08-08 | `Company/Decision-Records/WES-DEC-010.md` |
| `WES-DEC-011` | Mission Budget Envelope (estimate at intake, one approval, 80% notify, 100% hard-stop + PROMPT-ESC) supersedes per-call gating; per-run max_cost retired on implementation | 2026-08-08 | `Company/Decision-Records/WES-DEC-011.md` |

## Code / integration changes

| Change | PR | Merge | Deployed? |
|--------|----|-------|-----------|
| Seed `PROMPT-SYS` v2 (PROMPT-SYS-CORE) + idempotent `sync_prompt_sys()` in-place upsert | **#1** | **Merged (squash)** `9945792` on 2026-08-04 | **NO — held for combined final deploy** |
| Batch-0 close: ratified `PROMPT-SYS.md`, `WES-DEC-001/002`, INVENTORY | **#2** | **Merged (squash)** `99de3f9` on 2026-08-04 | **NO — docs only, no deploy** |
| Batch-1 (strategy): `FOUNDER-INTENT` + `COMPANY-PHILOSOPHY` (docs 03–04) | **#3** | **Merged (squash)** `43bb56b` on 2026-08-04 | **NO — docs only, no deploy** |
| Batch-2 (SOPs): `WES-DEC-003` + SOPs 05–10 | **#4** | **Merged (squash)** `714fdf5` on 2026-08-04 | **NO — docs only, no deploy** |
| CI coverage enforcement (WES-DEC-004): `pytest-cov` + `scripts/test.sh --cov-fail-under=71` | **#5** | **Merged (squash)** `0f661a8` on 2026-08-04 | **NO — CI tooling; no deploy** |
| Batch-3 docs (WES-DEC-005 + role prompts 11–23) | **#6** | **Merged (squash)** `65681cf` on 2026-08-04 | **NO — docs only** |
| Batch-4 docs (WES-DEC-007 + shared prompts 24–26) | **#7** | **Merged (squash)** `2322fbe` on 2026-08-04 | **NO — docs only** |
| Batch-5 docs (WES-DEC-008 + `TEST-MISSION-CHARTER`) | **#8** | **Merged (squash)** `9846f04` on 2026-08-06 | **NO — docs only** |
| Pre-flight 1: seed ratified Prompt Library (13 roles + TASK/REVIEW/ESC) via `sync_prompt_library()` — verbatim operative bodies | **#9** | **Merged (squash)** `d03325d` on 2026-08-06 | **Green (dev) only** — mission rebuild 2026-08-07, Founder-approved; production held |
| Pre-flight 2: load 6 SOPs + 3 governed docs into the Knowledge Engine via `sync_knowledge_library()` — verbatim full files | **#10** | **Merged (squash)** `bb97438` on 2026-08-07 | **Green (dev) only** — same rebuild; production held |
| Pre-flight 3: budget-gated provider ping (`ProviderPingService` + `POST /providers/{id}/ping`, Founder-only) | **#11** | **Merged (squash)** `aebb0dd` on 2026-08-07 | **Green (dev) only** — same rebuild; production held |

## Verification log

- **PROMPT-SYS-CORE / seed v2** — isolated throwaway-DB check **12/12 pass** (fresh insert v2,
  in-place update from old v1 stub, idempotent no-op, insert-if-missing); injection = **642 words**.
- **Full backend suite** (keyless sandbox, in-memory SQLite): **461 collected → 460 passed, 1 failed.**
  The one failure — `test_autonomous_engineering_atlas.py::test_execute_dry_run_is_side_effect_free`
  — is **environment-only** (`GitHubService.configured()` false without the App key) and **unrelated
  to this change**. Note: this checkout's backend suite is **461** tests (not the earlier "922" figure).

## Live-mission findings — TEST-MISSION-01 (2026-08-07; accepted by WES-DEC-010)

Recorded spend **$0.0855** (gated ping + 5 runs on `claude-opus-4-8`, ~$0.017 each) vs the $5/run cap
(WES-DEC-009). Evidence lives in the green DB (project `TEST-MISSION-01`; runs
`2e2cae92/5824c178/aa2d84d2/02fd8d61/274c9a1a`; thread messages retained per charter §7).

| # | Finding | Status |
|---|---------|--------|
| F1 | Green env was 3 days stale (image predated all pre-flight merges; libraries unseeded) | Fixed 2026-08-07 — rebuilt from `main aebb0dd` (+2 inert ATLAS migration files, zero ATLAS app code), idempotent seed synced (18 templates / SYS v2 / 13 roles / 9 governed docs) |
| F2 | Founder's earlier "ping" was reachability-only `/test` | Superseded — real budget-gated ping run ($0.000111, 21 tok, 1452 ms) |
| F3 | `python -m app.db.seed` prints "Seed skipped" while the sync upserts DO run | Open (misleading CLI message) |
| F4 | Budget was daily=$50/monthly=$1000/max=$5 vs charter "all limits $5" | Closed by **WES-DEC-009** (per-run $5 + hard_stop is the mission enforcement) |
| F5 | Intake endpoint: sync >60s; client timeout orphans a request that later COMMITS; duplicate-code retry → 63 s lock wait → `UniqueViolation` → bodyless 500 | Open (engineering item; UI's async decompose path avoids it) |
| **F6** | Executive-reasoning/planning LLM calls record **no** `provider_usage` — real spend invisible to budget counters (orchestration path records correctly) | Open — scoped PR, roadmap step 4 |
| F7 | Unhandled 500s produce empty bodies and **zero server logs** | Open (observability item) |
| F8 | Executive report mixes mission data with company-wide seed aggregates; similar-projects retrieval surfaces demo noise | Open (report scoping) |
| **F9** | **CENTRAL (charter §6.1):** composed prompts contain **none** of the ratified stack — no `PROMPT-SYS-CORE`, no `ROLE-*`, no `PROMPT-TASK`; runtime SOP = one-line `sop_library` stub; `prompt_version v1` | Open — **roadmap step 3: fix + mission run #2 as one package; wiring "complete" only when run #2's composed prompt shows CORE + ROLE + TASK** |
| F10 | Orchestration output is text only — charter §5's PR→merge gate unreachable by the engine (Development Engine exists, unverified end-to-end) | Open — scoped PR, roadmap step 4 |
| F11 | No inter-task artifact handoff (T004 proved it; fresh thread per task, `prior=[]`) | Open — scoped PR, roadmap step 4 |
| F12 | RBAC reality (§6.3/§6.4): AI employees are not API principals — permission walls face human operators (run/review = `exec:write` Director+); Operational read-only never engaged | Recorded — reframes the watch-trio items below |
| §6.5 | `seed_ai` divergence **confirmed live**: plan assigned to Ada/Turing/… ("AI CEO/CTO"); injected prompt says "You are Turing, AI CTO"; founder login is `WES-EMP-001 "Studio Director"` | Open — Founder reconciliation decision pending |
| §6.2 | Retrieval logged (13 rows/run) and surfaced ratified docs — but titles/summaries only; keyword LIKE; SOP slot `limit=5` of 6 | Open (retrieval wiring/depth) |
| + | Positives: QA plan-review verdict genuinely gated (plan blocked until Founder decision); executive reasoning quality high (caught the limit-vs-suffix ambiguity, unicode grapheme risk); T004 honestly reported missing inputs; review verdicts recorded (T004 `returned`) | — |
| + | Workflow gap: review outcomes do not advance `work_item.status` (tasks stuck `in_progress`) | Open (minor) |
| **F15** | Envelope scope `mission:<str(uuid)>` = 44 chars overflowed `budget_configs.scope` varchar(40) on Postgres at the 75d6f60 release gate; **SQLite fixtures don't enforce varchar widths**, so 579 green tests missed it. Release rolled back cleanly (0 rows leaked). | Fixed — scope = `mission:<uuid.hex>` (40 chars exactly) + loud in-code width guard + len==40 pinning test + real-Postgres INSERT proof |

## Pending actions — the reconciliation roadmap (WES-DEC-010, ordered)

1. **This docs PR** — findings ledger, WES-DEC-009/010, Status-line corrections. ✔ on merge
2. **Governed `truncate()` PR** — mission artifacts (T001 spec, T002 impl, T003 tests) → real
   SOP-CODING engineering PR, Founder-merged (the charter's PR gate, human-governed).
3. **F9 fix + mission run #2 — one package**; wiring proven only by run #2's composed prompt.
4. **F6 / F10 / F11** — one scoped engineering PR each.
5. **Combined production deploy — LAST, Founder-decided on evidence.** On deploy, confirm
   `PROMPT-SYS` v2 + the ratified libraries appear live (idempotent syncs; no destructive re-seed).

## Open items

- Pre-existing **ATLAS Sprint 02/03** work remains uncommitted in the `/opt/wes-green` working tree
  (separate from this program; intentionally not touched by these branches).
- **CI coverage enforcement (WES-DEC-004)** — **done**: `pytest-cov` added to `backend/requirements.txt`
  and `scripts/test.sh` wired with `--cov=app --cov-fail-under=71`. Delivered as the docs phase's
  **first code change, following `SOP-CODING` end-to-end** (branch `feature/coverage-ci-enforcement`;
  **PR #5 merged** `0f661a8`).
- **SOP-TESTING v2 learning (F15, Founder-directed 2026-08-08):** DB-boundary features need a
  **Postgres-parity check** — SQLite test fixtures do not enforce varchar widths (or several other
  constraints), so column-limit bugs pass a green suite and surface only at the production gate.
  Fold into the SOP-TESTING v2 revision: any feature writing new value *shapes* to existing
  columns ships either a real-Postgres test or an explicit in-code width/constraint guard with a
  pinning test (the F15 pattern).
- **Frontend coverage floor** — deferred (WES-DEC-004); set by ratchet after the frontend suite
  matures (revisit at the end of the Operating Instructions phase).
- **Watch (doc 27 live test) — OBSERVED 2026-08-07, reframed by F12:** the live mission showed AI
  employees are **not API principals** — every action executed under the human operator's token, so
  the trio's permission walls face humans (`exec:write` Director+), and Operational read-only never
  engaged at runtime. The original framing below is retained for the record; the reconciliation now
  rides the WES-DEC-010 roadmap. Original: Operational roles map to `EMPLOYEE` = **read-only** (WES-DEC-006).
  Observe in the doc 27 live end-to-end test (`TEST-MISSION-CHARTER`) whether this creates runtime
  friction — i.e. whether Operational employees' work flows cleanly through the gated workflow, or
  whether the read-only constraint needs a codified exception. Record the observation as a Founder
  decision at phase end. **Concrete instances (three):** the **QA Engineer** (`quality:review`), the
  **DevOps / Automation Engineer** (`devops:execute`), and the **Technical Writer** (`knowledge:write`)
  each have a core duty that maps to a **Lead/Director-level** permission they do not hold as Operational
  (`EMPLOYEE`); all three role prompts frame this as draft/prepare/verify (verdict), not an invented
  grant — these are the primary cases to watch and reconcile.
- **Code vs canonical role naming — CONFIRMED LIVE 2026-08-07 (mission §6.5):** the plan assigned
  tasks to the `seed_ai` cast (Ada/Turing/Hopper/… under "AI CEO / AI CTO") and the injected prompt
  literally read "You are Turing, AI CTO"; the founder login is employee `WES-EMP-001 "Studio
  Director"` with role=founder. Reconciliation remains a Founder decision (WES-DEC-010 roadmap).
  Original item: **Code vs canonical role naming — phase-end reconciliation (Founder decision).**
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
| 2026-08-04 | **Batch-3 (role prompts):** doc 22 `ROLE-DEVOPS-AUTOMATION-ENGINEER` v1.0 committed (Draft) — `devops:execute` Director-level gap framed honestly (prepare/verify, no invented grant); paired with the QA Engineer in the phase-end watch item; production deploy + rollback Founder-only; monitoring/health concrete. Deploy held. |
| 2026-08-04 | **Batch-3 (role prompts):** doc 23 `ROLE-TECHNICAL-WRITER` v1.0 committed (Draft) — `knowledge:write` Lead/Director-level gap (third watch instance, with QA + DevOps); Blueprint changes Founder-only (drafts only); first-person verbatim rule for Founder docs (SOP-DOCUMENTATION §2). **All 13 role prompts complete (docs 11–23)** — single Batch-3 PR next, on Founder approval. Deploy held. |
| 2026-08-04 | **Batch-3 merged:** **PR #6 merged** to `main` (`65681cf`) — Founder declared "merge = Batch-3 ratification". |
| 2026-08-04 | **Batch-4 (shared prompts) — WES-DEC-007:** Founder **ratified** the Role Prompt Library (role prompts 11–23); docs 11–23 marked **Ratified**. First commit of branch `docs/batch-4-shared-prompts`. Deploy held. |
| 2026-08-04 | **Batch-4 (shared prompts):** doc 24 `PROMPT-TASK` v1.0 committed (Draft) on `docs/batch-4-shared-prompts`. Deploy held. |
| 2026-08-04 | **Batch-4 (shared prompts):** doc 25 `PROMPT-REVIEW` v1.0 committed (Draft) on `docs/batch-4-shared-prompts`. Deploy held. |
| 2026-08-04 | **Batch-4 (shared prompts):** doc 26 `PROMPT-ESC` v1.0 committed (Draft) — **shared activity prompts complete (docs 24–26)**. Single Batch-4 PR next, on Founder approval. Deploy held. |
| 2026-08-04 | **Batch-4 merged:** **PR #7 merged** to `main` (`2322fbe`) — Founder declared "merge = Batch-4 ratification". |
| 2026-08-04 | **Batch-5 (test mission) — WES-DEC-008:** Founder **ratified** the shared activity prompts (docs 24–26); docs 24–26 marked **Ratified**. First commit of branch `docs/batch-5-test-mission`. Deploy held. |
| 2026-08-04 | **Batch-5 (test mission):** doc 27 `TEST-MISSION-CHARTER` v1.0 committed (Draft) — **all 27 Operating-Instructions documents now authored.** Observation-run charter for the first live end-to-end mission (Claude provider; $5 hard cap; `truncate()` utility + tests proposed). Pre-flight is separate post-ratification SOP-CODING PRs; production deploy still held. Single Batch-5 PR next, on Founder approval. |
| 2026-08-06 | **Batch-5 merged:** **PR #8 merged** to `main` (`9846f04`) — Founder declared "merge = Batch-5 ratification" (formally recorded in `WES-DEC-010`). Authoring phase closed: 27/27 documents merged. |
| 2026-08-06 | **Pre-flight 1 merged:** **PR #9** (`d03325d`) — ratified Prompt Library seeded via `sync_prompt_library()` (verbatim operative bodies; byte-equality fidelity tests). 496 passed, cov 73.04%. |
| 2026-08-07 | **Pre-flight 2 + 3 merged:** **PR #10** (`bb97438`) — 6 SOPs + 3 governed docs into the Knowledge Engine, verbatim full-file (509 passed, cov 73.12%); **PR #11** (`aebb0dd`) — budget-gated provider ping, Founder-only, hard-stop → 402 (515 passed, cov 73.20%). |
| 2026-08-07 | **Live mission TEST-MISSION-01 executed** (charter §5): green rebuilt from `main` + seeded (Founder-approved; F1); real gated ping; intake → AI planning (real Claude) → internal review (QA **rejected**) → Founder gate (QA spec pinned to T001; plan approved) → 5 real executions (`claude-opus-4-8`, $0.0855 total) → review verdicts (T004 `returned`). Findings **F1–F12** recorded (ledger above); central finding **F9** — ratified stack not injected. Budget enforcement per `WES-DEC-009`. |
| 2026-08-08 | **Roadmap steps 2–4 executed:** PR #13 (`eccc859`) governed `truncate()` landed from mission artifacts; PR #14 (`6f6c479`) **F9 wiring** — CORE+ROLE+TASK injected verbatim; **mission run #2 (`dbf275a6`) §6.1 VERDICT = PASS** (three layers byte-verbatim, personas retired, prompt_version v2, $0.0274 vs $0.0171 baseline); PR #15 (`86d8c32`) **F6 metering** — reasoning-path spend recorded via CostEngine. Frontend live snapshot: bundle byte-current, 218/218 endpoints match, no rebuild needed. |
| 2026-08-08 | **WES-DEC-011 (this PR):** Mission Budget Envelope approved (design + decision) — supersedes per-call gating; implementation = first post-deploy PR, before F10. **SOP library ratified (this PR):** `sync_sop_library()` upserts the 6 ratified SOPs' operative bodies (verbatim) into `sop_library`; legacy one-line stubs retired. |
| 2026-08-08 | **Post-mission reconciliation (this PR):** findings ledger added; `WES-DEC-009` (budget supersede) + `WES-DEC-010` (mission outcome, doc-27 ratification record, roadmap) created; doc 27 → **Ratified**; internal `Status: Draft` metadata corrected to **Ratified** across 26 docs; `knowledge_library_content.py` regenerated (verbatim full-file constants follow their sources). Deploy still held — roadmap step 5. |
