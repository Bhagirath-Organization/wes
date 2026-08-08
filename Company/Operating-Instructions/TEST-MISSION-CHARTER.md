# TEST-MISSION-CHARTER — First Live End-to-End Mission

| Field | Detail |
|-------|--------|
| **Document ID** | TEST-MISSION-CHARTER (doc 27 of 27) |
| **Author** | WES Constitutional Committee |
| **Status** | Ratified — `WES-DEC-010` (2026-08-08) |
| **Governance** | Governed charter for the first live mission. Subordinate to the Blueprint, `PROMPT-SYS`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, and the SOPs. |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & mindset
This charter governs the **first live end-to-end run** of the full WES governance stack — `PROMPT-SYS-CORE` + a Role Prompt + the activity prompts + the six SOPs + the real gates — driving a real LLM on a real, tiny task.

**This is an observation run, not an exam.** Success is a **complete, honest record of what worked and what broke** — not a completed task. **A failure with evidence is a successful test.** Nothing is hidden; nothing is retried-until-green to look good; there is no "10/10 READY". That sentence-level honesty is the entire point of this phase (COMPANY-PHILOSOPHY value 7; PROMPT-SYS §21).

## 2. The mission (stated as a real intake)
- **Objective:** add one small, pure utility function with tests to the backend.
- **Proposed function (awaits Founder approval — see Open Founder Decisions):** `truncate(text: str, limit: int, suffix: str = "…") -> str` — return `text` unchanged if within `limit`, else cut to `limit` and append `suffix`. Pure logic; no external services, schema change, or security surface; it generalizes the inline clipping already in `company_brain._clip`.
- **File (layered architecture):** new module `app/core/text.py`.
- **Tests (SOP-TESTING §3):** `backend/tests/unit/test_text.py`.
- **Acceptance criteria (testable):** (1) text ≤ `limit` returned unchanged; (2) longer text cut to `limit` + `suffix`; (3) boundary at exactly `limit`; (4) empty string handled; (5) `./scripts/test.sh` green, backend coverage floor ≥ 71% (WES-DEC-004).
- **Scope boundary:** this one function + its tests. **Nothing else** — no wiring, no refactor, no other file.

## 3. Configuration
- **Provider: Claude (Anthropic)** via the existing Provider Platform; the API key is **encrypted at rest** (`app/core/secrets.py` Fernet; `app/models/provider_platform.py`; SOP-SECURITY §3). Configuring it is `orch:write` — **Founder-only**; the Founder performs it.
- **Budget: a hard cap of $5 (USD)** via the real budget gate (`budget_service.py` — `BudgetConfig.max_cost` / `daily_cost_limit` / `monthly_cost_limit`; spend summed from `estimated_cost` USD). Breach raises `BudgetExceededError` → **automatic abort** (§8).
- **Environment: development / staging only.** Production untouched; the **deploy-hold continues** (INVENTORY policy).

## 4. Pre-flight (prerequisites — each a separate post-ratification engineering PR under SOP-CODING)
Not part of this docs PR. After ratification, each prerequisite is its own engineering PR following **SOP-CODING end-to-end** (PR #5 precedent), **merged by the Founder** before execution:
1. **Seed the Prompt Library with the ratified content** — `PROMPT-SYS` v2 (already seeded), the 13 role prompts, and `PROMPT-TASK`/`REVIEW`/`ESC` — via the `seed_execution.py` upsert pattern (the `sync_prompt_sys()` precedent: idempotent, in-place).
2. **Load the six SOPs + governed docs into the Knowledge Engine** so retrieval has real content. Honestly: retrieval is **keyword-only today** (`knowledge.py` — "Awaiting semantic-search backend") — its quality is itself observed (§6.2).
3. **Verify provider connectivity** with a minimal ping **under the budget gate** (a few tokens, far below $5).

## 5. Execution flow (expected path, with the real gates)
Mission intake (`FounderOSService.submit_objective` — business intent only) → plan → **Founder plan approval — GATE** (Founder-only, PROMPT-SYS §6) → **task execution:** `PROMPT-SYS-CORE` + the Backend Engineer **ROLE** prompt + `PROMPT-TASK` composed and injected (composition: `orchestration.py` `build()` — prompt template + SOP + decision rules + retrieved knowledge) → **SOP retrieval** (`RetrievalService.retrieve_for`, keyword) → **code** per SOP-CODING → **tests** per SOP-TESTING (red→green, full suite, coverage floor) → **review board verdicts** (`ReviewStatus`) per `PROMPT-REVIEW` / SOP-REVIEW → Pull Request → **Founder merge decision — GATE** (`dev:approve`, Founder-only). Any escalation arrives in the `PROMPT-ESC` six-field package.

## 6. Observation list (each with the evidence to capture)
1. **Injection** — did the stack actually deliver **CORE + ROLE + TASK** to the model? *Evidence:* the composed prompt sent to the provider. (Today `build()` fetches `PROMPT-TASK` + `SOP-CODE`; whether the full CORE+ROLE+TASK stack is delivered is what we check.)
2. **Retrieval, unprompted** — did the employee retrieve the right SOPs on its own? *Evidence:* the retrieval calls and what came back (the retrieval-wiring question).
3. **The three-role RBAC watch trio** — QA `quality:review`, DevOps `devops:execute`, Technical Writer `knowledge:write`: where does the workflow hit these walls? *Evidence:* the exact point + permission error.
4. **Operational = read-only friction** — did work flow through the gated workflow, or stall? *Evidence:* where a write was needed and how it was authorized.
5. **`seed_ai.py` naming divergence** — does the code's `CEO`/`CTO`/`Chief Architect` model surface anywhere live vs the canonical org? *Evidence:* any mismatch observed.
6. **Cost** — actual spend vs the $5 cap; where tokens went. *Evidence:* `estimated_cost` per call (`cost_tracking`).

## 7. Evidence & reporting
A full **5-part report**; **every model call's transcript is retained.** Every observed failure is recorded **with evidence** (INVENTORY open items or a `WES-DEC-###`). Findings feed the **post-phase v2 revisions**. No result is asserted without evidence (PROMPT-SYS §13, §21).

## 8. Abort conditions
**Automatic abort:** the **$5 budget cap** is hit (`BudgetExceededError`); any **SOP-SECURITY §8 prohibited action** is attempted (disable a check, route a test key to prod, output a secret); or a **runaway loop** (same failure repeating without progress). **Manual:** the **Founder may abort at any moment, no justification needed.** On abort: **STOP**, **preserve all evidence**, report per §7. **An abort is a valid test outcome**, not a failure of the test.

## 9. After the mission
Findings are reviewed with the Founder; the phase-end reconciliations are decided **on this evidence** — the three-role RBAC trio, the `seed_ai.py` naming, the retrieval-wiring next steps. Only then does the **single combined production deploy** question go to the Founder — the deploy that lifts the hold and applies `PROMPT-SYS` v2 to green.

## Appendix — Referenced Documents
`PROMPT-SYS.md` §6/§13/§21; `PROMPT-SYS-CORE.md`; `FOUNDER-INTENT.md` §4; `COMPANY-PHILOSOPHY.md` value 7; `SOP-CODING.md`; `SOP-TESTING.md` §3; `SOP-SECURITY.md` §3/§8; `SOP-DEPLOYMENT.md`; `ROLE-BACKEND-ENGINEER.md`; `PROMPT-TASK.md` / `PROMPT-REVIEW.md` / `PROMPT-ESC.md`; `app/services/budget_service.py`, `app/models/orchestration.py` (`cost_tracking`), `app/services/orchestration.py` (`build`), `app/services/knowledge.py`, `app/services/founder_os.py`, `app/core/secrets.py`, `app/models/provider_platform.py`, `app/db/seed_execution.py`; `INVENTORY.md`.

## Open Founder Decisions
- **Proposed test function** — `truncate(text, limit, suffix="…")` in `app/core/text.py` awaits Founder approval; the Founder may approve or swap it at review.
- **Budget-limit field** — whether the $5 hard cap is set as `max_cost` (per-run) or `daily_cost_limit` / `monthly_cost_limit` in `BudgetConfig` — the Founder sets it at configuration (`orch:write`).
- Phase-end reconciliations (trio RBAC, `seed_ai.py` naming, retrieval wiring) are decided **after** the mission on its evidence (§9).
