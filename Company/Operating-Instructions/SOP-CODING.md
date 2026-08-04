# SOP-CODING — Standard Operating Procedure for Software Development

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-CODING (doc 05 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Draft — Founder ratification pending |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → this SOP |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose
Defines the mandatory procedure for writing, modifying, reviewing, or refactoring software inside WES, so any two AI Engineers produce the same engineering discipline. It adds only procedure specifics the governing documents lack.

## 2. Applicability
Mandatory for the Backend Engineer, Frontend Engineer, AI Engineer, DevOps / Automation Engineer (when modifying code), Security Engineer (when fixing code), and any future coding AI Employee (PROMPT-SYS §7).

## 3. Preconditions — verify ALL before touching code; if any fails, STOP and escalate (PROMPT-SYS §9, §20)
1. Task approved, and you are its single owner (COMPANY-PHILOSOPHY value 3).
2. Execution Plan approved — engineering without an approved plan is forbidden (PROMPT-SYS §9).
3. Repository Intelligence complete for the target repository.
4. Architecture understood; context loaded in the order of PROMPT-SYS §10.
5. Correct repository selected (WES and WORLD are independent — PROMPT-SYS §6); no WORLD engineering unless FOUNDER-INTENT §4 permits.
6. Feature branch created (§6); repository write permission available.

## 4. Coding Workflow — mandatory sequence, no step skipped (COMPANY-PHILOSOPHY value 6)
Retrieve Context → Understand Architecture → Reuse Existing Components → Design → Implement → Self-Review → Unit Test → Integration Test → Documentation Update → Commit → Pull Request → Quality Gates → Founder Approval → Merge. Merge and production are Founder-only (PROMPT-SYS §6).

## 5. Coding Rules
- Reuse before building; never duplicate existing code or modules (PROMPT-SYS §8).
- Never bypass the architecture; stay within the existing layers (`app/api`, `app/services`, `app/models`, `app/schemas`, `app/repositories`, `app/domain`, `app/db`).
- One task = one focused change (PROMPT-SYS §8).
- Match the naming and idiom of surrounding code. Python line length **100** (black); code must pass `ruff` (rules `E`, `F`, `I`).
- No hardcoded values or secrets; use environment configuration (PROMPT-SYS §8, §17).
- Explicit error handling; comment the *why*, not the *what* (PROMPT-SYS §8).
- Justify any new dependency against what already exists; follow licensing (Blueprint Vol 08).
- Prefer additive, backward-compatible change (e.g. `backend/alembic/versions/` migrations); refactoring is its own focused commit with tests.

## 6. Git Rules (Blueprint Vol 04; PROMPT-SYS §8–§9)
- Branch from `main` per task: `feature/<name>`, `fix/<name>`, or `docs/<name>`. `main` is protected and always releasable.
- Commit format: `type(scope): summary` (e.g. `feat(auth): add login endpoint`). Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Small, logical commits.
- No direct commit to `main`; no force-push; no history or branch deletion by the engineer (PROMPT-SYS §9).
- Open a Pull Request; merge to `main` only after review, passing checks, and Founder approval (PROMPT-SYS §6).

## 7. Definition of Good Code
Simple, reliable, disciplined (COMPANY-PHILOSOPHY §3): small and clear; reuses existing components; consistent with the architecture; tested; documented; traceable; lint/format/type-clean; no secrets.

## 8. Definition of Bad Code — refactor or reject on sight
Duplicate logic; magic numbers / hardcoded values; hidden dependencies; dead or unused code; oversized functions; architecture violations; missing tests; missing documentation.

## 9. Security During Coding (PROMPT-SYS §17; Blueprint Vol 08)
Secrets via environment variables only. Validate all input. Enforce authentication and authorization on protected paths. Validate and justify dependencies. Code must clear the security review engines (`app/services/quality_review_engines.py`): secrets CWE-798, SQL injection CWE-89, command injection CWE-78, path traversal CWE-22.

## 10. Testing Requirements
- Cover new behaviour with unit and integration tests (Blueprint Vol 08: unit, integration, end-to-end, manual/review).
- Run before commit: `./scripts/test.sh` (backend `pytest -q` over `backend/tests`; frontend `vitest`). Regression: the full suite must pass with no reduction in passing tests.
- Never claim an unobserved pass (PROMPT-SYS §20; COMPANY-PHILOSOPHY value 7). On failure: fix root cause → re-test.
- **Coverage threshold: Not defined — Founder decision needed.** (`backend/pyproject.toml` `[tool.coverage.run] source=["app"]` sets scope but no `fail_under`.)

## 11. Documentation Requirements (Blueprint Vol 09; PROMPT-SYS §14)
Every code change updates the affected documentation as part of the change: API docs, architecture notes, module `README`, and a Decision Record (`WES-DEC-###` / ADR) for significant or hard-to-reverse decisions.

## 12. Quality Gates
Gates are Blueprint Vol 08 (4 gates) and PROMPT-SYS §22. Coding STOPS and cannot progress when: `./scripts/lint.sh` is non-zero; any test fails; the review board is not unanimous; or a known unresolved security finding exists. Merge/release requires Founder approval (PROMPT-SYS §6).

## 13. Failure Handling
Per PROMPT-SYS §20 and PROMPT-SYS-CORE (FAILURE). SOP-specific triggers: compilation/type failure → fix before proceeding; test failure → root-cause loop; architecture/repository/dependency/merge conflict → resolve on the branch, never force; unknown behaviour or ambiguous requirement → escalate, do not guess (FOUNDER-INTENT §6); unmet precondition → abort (§3).

## 14. Outputs (PROMPT-SYS §14; PROMPT-SYS-CORE OUTPUT)
Every execution produces: modified files (precisely identified), tests executed with real results, updated documentation, a commit, a Pull Request, and evidence (COMPANY-PHILOSOPHY value 7). Handoffs use PROMPT-SYS §18.

## 15. Definition of Done
As defined in PROMPT-SYS §22 and Blueprint Vol 04 (DoD) + Vol 08 (Quality Gates). Done requires all of them and Founder approval of the release.

## 16. Examples (real repository references)
- **Good execution — reuse, never duplicate:** `app/services/company_brain.py` ("Reused, never duplicated: ExecutiveReasoningService … ArchitectureService / DependencyService"); `app/services/autonomous_engineering.py` ("Built on top of existing engine, nothing rebuilt"). These follow §4–§5.
- **Escalation / abort — precondition failure:** `app/services/engineering_execution.py` `preconditions()` raises `EngineeringAbort`; `POST /api/v1/engineering/plans/{id}/execute` returns `422 — "Cannot execute — precondition failed: Repository write permission available"` when the GitHub App is not configured. This is the correct STOP of §3/§13.
- **Bad execution:** No repository example exists yet — the codebase is maintained to this SOP; §8 lists the anti-patterns to reject.

## 17. Appendix — Referenced Documents
`Company/Operating-Instructions/PROMPT-SYS.md`; `PROMPT-SYS-CORE.md`; `FOUNDER-INTENT.md`; `COMPANY-PHILOSOPHY.md`; Blueprint Vol 04 (Engineering System), Vol 08 (Security & Quality), Vol 09 (Knowledge Management); `scripts/lint.sh`, `scripts/format.sh`, `scripts/test.sh`; `backend/pyproject.toml`; SOP-CODE (Prompt/SOP Library seed, `app/db/seed_execution.py`).

## Open Founder Decisions
- **Test coverage threshold** (`fail_under` %, backend and frontend) — Not defined — Founder decision needed.
