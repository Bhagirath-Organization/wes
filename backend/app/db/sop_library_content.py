"""Verbatim operative bodies of the ratified WES SOPs for the runtime SOP library.

Generated from ``Company/Operating-Instructions/SOP-*.md`` by extracting each
doc's operative body — the PROMPT-SYS-CORE seeding boundary (drop title,
metadata table, Appendix, Open Founder Decisions; keep every procedure section
byte-for-byte). See :func:`extract_sop_body`. These retire the legacy one-line
``sop_library`` stubs via the idempotent ``sync_sop_library`` upsert; the
fidelity tests re-derive every body from the live docs and fail on drift.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.execution_enums import SOPCategory

_APPENDIX = re.compile(r"^## (\d+\. )?Appendix")


def extract_sop_body(text: str) -> str:
    """Operative body of a ratified SOP doc: from the first ``## `` heading after
    the metadata rule up to (not including) the numbered ``## N. Appendix``
    heading. Byte-for-byte from the file; doc chrome (title, metadata table,
    appendix, open decisions) is dropped — the PROMPT-SYS-CORE seeding boundary.
    """
    lines = text.splitlines()
    meta_end = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
    body_start = next(i for i in range(meta_end + 1, len(lines)) if lines[i].startswith("## "))
    appendix = next(i for i in range(body_start, len(lines)) if _APPENDIX.match(lines[i]))
    return "\n".join(lines[body_start:appendix]).strip("\n")


@dataclass(frozen=True)
class SOPSpec:
    """A ratified SOP to seed: runtime code, source doc, title, category, body."""

    code: str
    source_doc: str
    title: str
    category: SOPCategory
    content: str
    version: int = 2


SOP_CODE = """## 1. Purpose
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
- **Coverage floor: backend line coverage ≥ 71%** (ratchet, WES-DEC-004; baseline 73%); **frontend deferred** (WES-DEC-004).

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
- **Bad execution:** No repository example exists yet — the codebase is maintained to this SOP; §8 lists the anti-patterns to reject."""

SOP_REVIEW = """## 1. Purpose & Scope
Defines the mandatory procedure for reviewing work inside WES — code review, document review, and the review-board verdict — so any two reviewers apply the same bar. Procedure only. Scope: every Pull Request and every review-gated change.

## 2. Applicability — who reviews what (authority per PROMPT-SYS §7)
- **Software Architect** — technical changes; owns final approval for significant changes (Blueprint Vol 04).
- **QA Engineer** — release quality; owns release-quality sign-off.
- **Security Engineer** — the security gate; clears security findings.
- **Studio Director** — operational and cross-department decisions.
- **Peer engineers** — first-line correctness and clarity review.
Each acts only within its authority; beyond it, escalate (AI Decision Hierarchy).

## 3. Preconditions — a review starts only when ALL hold; else return to author
1. Pull Request open against the correct base (SOP-CODING §6).
2. Full suite run with evidence attached — real observed counts (SOP-CODING §10). No evidence, no review.
3. Author self-review done (SOP-CODING §4).
4. Context attached in the PROMPT-SYS §18 handoff structure (Context, Decision, Evidence, Pending Work, Expected Outcome).

## 4. Review Workflow — mandatory sequence
PR opened → automated checks green (`./scripts/lint.sh`, `./scripts/test.sh`) → the **six review engines** run over the real diff (`app/services/quality_review_engines.py`: Architecture, Code, Security, Performance, Dependency, Documentation `ReviewService`), each emitting findings with a `FindingSeverity` → the reviewer reads every finding and the diff → applies the §5 criteria → records a verdict (§6). On approval the change proceeds to the Founder gate; a reviewer never merges (PROMPT-SYS §6, §9). Findings are fixed or explicitly waived with a reason; the author may not waive a security finding (§6).

## 5. Review Criteria — the reviewer walks this checklist
1. **Correctness** against the task's acceptance criteria.
2. **Architecture consistency** — within the existing layers; no violation (SOP-CODING §5).
3. **Reuse** — no duplication of existing code or modules (PROMPT-SYS §8).
4. **Tests** present (happy / failure / boundary) and genuinely passing with evidence (SOP-CODING §10; COMPANY-PHILOSOPHY value 7).
5. **Documentation** updated as part of the change (SOP-CODING §11).
6. **Security** — engine findings cleared; no secret, no unresolved CWE (SOP-CODING §9).
7. **Code quality** — conforms to SOP-CODING §7; contains none of §8.

## 6. Verdicts — the exact outcomes (recorded as `ReviewStatus`)
- **approve** → `approved` — all §5 criteria met; issued by any reviewer within scope.
- **request changes** → `changes_requested` — specific, actionable findings; the default when any §5 item fails.
- **reject** → `rejected` — wrong in premise or violates a non-negotiable (FOUNDER-INTENT §6).
- **escalate** — the decision exceeds the reviewer's authority (PROMPT-SYS §15); a handoff up the AI Decision Hierarchy, not a `ReviewStatus`.

Recorded via `POST /api/v1/reviews/{review_id}/decision`. **Review-board unanimity:** where the board applies — the four reviewers **AI Chief Architect, AI QA Engineer, AI Security Engineer, AI Performance Reviewer** — it is **approved only if all four approve** (`all(verdict == "approved")`, `app/services/autonomous_engineering.py`); any non-approval **blocks**. Merge and release still require Founder approval (PROMPT-SYS §6).

## 7. Reviewer Rules
- Review the **work, not the author**.
- **Evidence over claims** (COMPANY-PHILOSOPHY value 7): verify the stated tests and results; an unverified claim is treated as not yet true.
- **No rubber-stamping** — each reviewer has authority to BLOCK and must use it; a verdict with no findings on non-trivial work must state **what was checked** against §5.
- Findings are specific and actionable: file/line, the rule broken, the fix.

## 8. Failure & Disagreement Handling
- **Author disputes a finding:** respond on the PR with evidence; the reviewer re-reviews. Unresolved → escalate to the Software Architect (technical) or the relevant lead (PROMPT-SYS §15).
- **Repeated rejection:** after the same change is rejected twice for the same root cause, escalate rather than re-submit (do not re-litigate — PROMPT-SYS §11, §16).
- **Non-negotiable at risk / beyond authority:** escalate to Studio Director → Founder (PROMPT-SYS §15; FOUNDER-INTENT §6).

## 9. Outputs — a completed review records
The verdict (`ReviewStatus`), findings with severity, what was checked (§5), the evidence reviewed, and the reviewer identity — on the PR / review record (PROMPT-SYS §19). Nothing significant is verbal (PROMPT-SYS §18).

## 10. Definition of Done for a review — cite
Done when a verdict is recorded with findings and rationale, all CRITICAL/HIGH findings are resolved or explicitly waived by the reviewer who owns that gate (Architecture → Software Architect, Security → Security Engineer, Quality → QA Engineer), never by the author — every waiver records the reason on the PR — and, for merge, the required approvals plus Founder approval exist (PROMPT-SYS §6, §22; SOP-CODING §15).

## 11. Examples (real)
- **Engine blocks a real risk:** `app/services/quality_review_engines.py` `SecurityReviewService` flags a hardcoded secret as `FindingSeverity.CRITICAL` (CWE-798); a reviewer must not approve until it is cleared (§6).
- **Unanimous board:** `app/services/autonomous_engineering.py` `review_board()` — four reviewers, each told "You have authority to BLOCK. Do not rubber-stamp"; `approved = all(r["verdict"] == "approved")`; one `changes_requested` populates `blocking` and stops merge-readiness.
- **Verdict record:** `POST /api/v1/reviews/{review_id}/decision` writes a `ReviewStatus` (`approved` / `changes_requested` / `rejected`).
- **Human-PR rejection:** No repository example exists yet — this program's PRs (#1–#3) were Founder-approved; the bar in §5 still applies."""

SOP_TEST = """## 1. Purpose & Scope
Defines how software is tested inside WES — what tests are written, what is run, and what counts as a genuine pass — so results are reproducible and trustworthy. It is the detailed home for the testing rule SOP-CODING §10 summarises. Scope: every code change.

## 2. Applicability
Every coding role (SOP-CODING §2) writes and runs tests for its own changes. The **QA Engineer** owns release-quality sign-off (PROMPT-SYS §7; SOP-REVIEW §2).

## 3. Test Types & when each is mandatory (Blueprint Vol 08)
- **Unit** — every new or changed unit of logic. Location: `backend/tests/unit/`; frontend `frontend/src/__tests__/*.test.tsx`.
- **Integration** — any change crossing modules, API, or DB. Location: `backend/tests/api/` (API + DB via `TestClient`) and `backend/tests/integration/`.
- **End-to-end** — user-facing flows (frontend component/route tests, e.g. `Login.test.tsx`).
- **Regression** — the full existing suite, every change (§6).
- **Manual verification** — where automation is impractical; recorded with evidence.
Run commands: backend `pytest -q` (`pyproject.toml` `testpaths=["tests"]`, `addopts="-q"`); frontend `vitest run`; both via `./scripts/test.sh`.

## 4. Writing Tests
- Cover the **happy path, failure path, and boundary** of the new behaviour.
- **Prove the test tests something:** it must **fail before the fix and pass after** (red → green). A test that passes without the change is not evidence.
- **Naming & placement (from the real suite):** files `test_<area>.py`, functions `def test_<behaviour>()`; place beside peers in `unit/`, `api/`, or `integration/`.
- **Reuse fixtures, never duplicate setup** (PROMPT-SYS §8): `client`, `as_role`, `SessionFactory`, `db_session`, and the `*_seeded` fixtures in `backend/tests/conftest.py`. Backend tests use the in-memory SQLite `engine` from `conftest.py`; no external services.

## 5. Running & Reporting
- Run the **FULL suite before every commit** — never a subset (SOP-CODING §10).
- **Report exact observed counts** — collected / passed / failed / skipped, from the real run. **Never claim an unobserved pass** (PROMPT-SYS §20, §21; COMPANY-PHILOSOPHY value 7).
- **Environment-only failures** (a check needing a credential absent from the sandbox) are **identified as such with evidence** — the failing test id, the reason, and proof it is environmental — never hidden and never silently counted as a pass.
- A failing test blocks the commit unless it is a documented environment-only failure with evidence.

## 6. Regression Rule
**No reduction in passing tests.** A previously passing test that now fails **blocks the change** until fixed or proven environment-only (§5). New behaviour ships with new tests; removing a test requires a recorded reason.

## 7. Coverage
- **Backend line coverage floor ≥ 71%** (ratchet, WES-DEC-004; baseline 73%). Frontend floor **deferred** (WES-DEC-004).
- **Measure with:** `coverage run --source=app -m pytest` then `coverage report` (`pyproject.toml` `[tool.coverage.run] source=["app"]`).
- CI enforcement is **live**: `./scripts/test.sh` runs the backend suite with `--cov=app --cov-fail-under=71` (WES-DEC-004).

## 8. Test Failure Handling
- **Root-cause loop:** fail → diagnose root cause → fix → re-test until it genuinely passes (PROMPT-SYS §20). Never claim a pass that was not observed.
- **Flaky tests:** a test that passes and fails non-deterministically is **identified, recorded as an open item, and quarantined honestly** (skipped with a linked reason) — **never deleted** to make the suite green. A quarantined test is an open item to fix, not a resolved one.
- **Unmet precondition or unknown behaviour:** escalate, do not guess (PROMPT-SYS §15; FOUNDER-INTENT §6).

## 9. Outputs — test-run evidence in the 5-part report
Every execution's Verification section states: the **exact command run**, the **collected / passed / failed / skipped** counts, any **environment-only failures** (id + reason + evidence), and the **coverage %** if measured. Evidence, not assertion (COMPANY-PHILOSOPHY value 7).

## 10. Examples (real)
- **Real suite shape:** `backend/tests/` — `unit/` (12 files), `api/` (38), `integration/` (2); shared fixtures in `conftest.py` (in-memory SQLite `engine`, `client`, `as_role`, `*_seeded`). Frontend: `frontend/src/__tests__/*.test.tsx` via `vitest run`.
- **Red→green naming:** `backend/tests/unit/test_secrets.py` — `test_encrypt_decrypt_round_trip` (happy) and `test_wrong_key_cannot_decrypt` (failure path).
- **Environment-only failure (identify, don't hide):** `tests/api/test_autonomous_engineering_atlas.py::test_execute_dry_run_is_side_effect_free` returns 422 because `GitHubService.configured()` is false without the GitHub App key — reported as environment-only with the 422 evidence, not counted as a pass.
- **Observed baseline:** full suite = **461 collected, 460 passed, 1 (environment-only) failed**; coverage **73%** (`coverage run --source=app -m pytest`)."""

SOP_DEPLOY = """## 1. Purpose & Scope
Defines how anything reaches staging and production inside WES — the procedure around the DevOps pipeline (build → release → deploy → verify → rollback). Procedure only. Scope: every deployment to staging or production.

## 2. Applicability
The **DevOps / Automation Engineer** executes builds, pipelines, and staging deploys (`devops:execute`, Founder + Director). **Production deploy and rollback are Founder-only** (`devops:production`; PROMPT-SYS §6). Per `app/models/devops.py`: "All production deployment is Founder-gated; nothing is pushed or deployed to a real production host."

## 3. Preconditions — a production deploy proceeds only when ALL hold (PROMPT-SYS §22)
1. Change **merged to `main`** (SOP-CODING §6).
2. **Full suite green** (SOP-TESTING §5) and **quality gates passed** (SOP-CODING §12).
3. **Release notes prepared** (Blueprint Vol 04).
4. **Founder release approval recorded** — production is a Founder-only gate (PROMPT-SYS §6).
A pipeline runs only for a task whose status is `approved`, `merged`, or `deployed` (`devops_pipeline.py`).

## 4. Deployment Workflow — the pipeline stages as implemented (`app/services/devops_pipeline.py` `_STAGES`)
`build → unit_tests → integration_tests → security_scan → docker_image → artifact → release_candidate → staging_deploy → monitoring → rollback_ready → production_approval`.
- Trigger: `POST /api/v1/devops/pipelines/run` (`devops:execute`). Each stage is recorded with a `StageStatus` (`pending/running/passed/failed/skipped`); **a failing stage stops the pipeline and raises an Incident**.
- **Staging deploys automatically**; the pipeline then halts at `production_approval` (`PipelineStatus.awaiting_production`) — the Founder gate.
- **Production** is released by a separate Founder-only action: `POST /api/v1/devops/pipelines/{id}/deploy-production` (`devops:production`). The `Deployment` must be `awaiting_approval`; the deployer extracts the artifact and runs `verify_deployment` before it becomes `deployed` (`devops_deploy.py`), strategy `blue_green` (`DeployStrategy`).
- Evidence per stage: build (`BuildStatus`), release (`ReleaseStatus`), deployment (`DeploymentStatus`), health, and the artifact.

## 5. Environment Rules (`Environment` enum)
- **development / testing** — local + in-memory test DB; no real credentials.
- **staging** — auto-deployed by the pipeline; the last check before production (current stack: `wes-staging`).
- **production (blue-green)** — `docker-compose.green.yml` (`wes-green-db` / `wes-green-backend` / `wes-green-frontend`); the Blueprint is mounted **read-only** (`/app/Blueprint:ro`) — never modified by deploy (PROMPT-SYS §9). VPS scripts live in `deploy/vps/`.
- Config via **environment only**, never in code (PROMPT-SYS §17; `.env.green`).
- **Deploy-hold policy (current):** during the Operating Instructions phase, changes merge but production is **held** for one combined end-of-phase deploy (INVENTORY policy). Nothing is deployed until the Founder calls it.

## 6. Verification After Deploy
- Run `./scripts/health.sh` → `logs/health-report.txt` (exit 0 = healthy); health covers `app_status`, `api_status`, `db_status`, `provider_status` (`HealthCheck`), plus `deploy/vps/verify.sh`.
- Confirm the **specific change is live** — e.g. after the PROMPT-SYS v2 seed, verify `PROMPT-SYS` shows **version 2** in the live `/execution` Prompt Library.
- A deploy is not "done" until verified with evidence (COMPANY-PHILOSOPHY value 7; PROMPT-SYS §22).

## 7. Rollback
- **Mandatory** when post-deploy health fails, verification fails, or a production incident is raised.
- Mechanism: `POST /api/v1/devops/rollback` (`devops:production`, Founder) to a prior `to_release_id`; records `RollbackHistory` and sets `DeploymentStatus.rolled_back` / `ReleaseStatus.rolled_back`.
- **Who decides:** the Founder (production is Founder-gated). The DevOps Engineer executes and records the reason and outcome.

## 8. Failure Handling
- **Failed build / test / security_scan / deploy stage** → the pipeline stops at that stage (`StageStatus.failed`, `PipelineStatus.failed`) and raises an Incident; fix the root cause and re-run (PROMPT-SYS §20). Never claim an unobserved success.
- **Partial or failed production deploy** → roll back (§7); do not leave production half-changed.
- **Never "fix forward" on production without Founder approval** — any production change is a Founder-only gate (PROMPT-SYS §6).

## 9. Outputs — the deployment record
Pipeline id + per-stage `StageStatus`, the build + artifact, the `Release` (version, `ReleaseStatus`), the `Deployment` (`Environment`, `DeploymentStatus`, strategy), the post-deploy health report, the Founder approval reference, and — on failure — the `Incident` and any `RollbackHistory`. On the record, never verbal (PROMPT-SYS §18, §19).

## 10. Examples (real)
- **The held PROMPT-SYS v2 deploy:** PR #1 (`9945792`) merged the v2 seed to `main` but **was not deployed** — held per the deploy-hold policy. On the eventual Founder-approved deploy, `seed_execution()` → `sync_prompt_sys()` updates `PROMPT-SYS` to **v2 in place**; then verify v2 in the live `/execution` Prompt Library.
- **Blue-green production:** `docker-compose.green.yml` (`name: wes-green`, `wes-green-backend:latest`), Blueprint mounted `:ro`.
- **Founder-only endpoints:** `POST /devops/pipelines/{id}/deploy-production` and `POST /devops/rollback` require `devops:production` (Founder); `POST /devops/pipelines/run` requires `devops:execute` (Founder + Director)."""

SOP_DOCS = """## 1. Purpose & Scope
Defines how documentation is written and maintained inside WES — code docs, operating documents, decision records, and the INVENTORY register — so the record is consistent, current, and trustworthy. Procedure only. Scope: every document produced or changed inside WES.

## 2. Applicability
Every role documents its own work; the **Technical Writer** owns the knowledge base and keeps the Blueprint and company docs current (Blueprint Vol 09; PROMPT-SYS §7). **Founder-authored governed documents are committed verbatim** — never rewritten, improved, or committee-reviewed by AI; only broken Markdown is fixed. Precedent: FOUNDER-INTENT v1.0 and COMPANY-PHILOSOPHY v1.0 (WES-DEC-003). Changing a Founder's words changes Founder intent, which is prohibited.

## 3. Document Types & exact homes
- **Code docs** — module `README`, docstrings, and API docs, beside the code (`backend/app/…`, `frontend/src/…`).
- **Implementation / dev docs** — `docs/implementation/`, `docs/dev/`, `docs/releases/`.
- **Operating Instructions** — `Company/Operating-Instructions/` (the Constitution, governed docs, `SOP-*`, INVENTORY).
- **Decision Records** — `Company/Decision-Records/WES-DEC-###.md` (real: WES-DEC-001…004).
- **Employee profiles** — `Employees/<Role>/README.md`.
- **Phase register** — `Company/Operating-Instructions/INVENTORY.md`.

## 4. Writing Rules
- **Markdown, stored in Git beside the work** it describes (PROMPT-SYS §14; Blueprint Vol 09).
- **Professional and factual** — no fluff, no motivational language, and **no self-assessment sections** (no scorecards or "READY" verdicts) (PROMPT-SYS §14).
- **Metadata table first** — every governed doc / SOP opens with the standard table (Document ID, Author, Status, Governance, Version), as in `PROMPT-SYS.md` and the SOPs.
- **Cite, don't restate** — where a higher document states a rule, cite it in one line.
- **State assumptions and unknowns**; write "Not defined — Founder decision needed" rather than invent a value (PROMPT-SYS §21).

## 5. Decision Records (WES-DEC)
- **Required when** a decision is significant, cross-cutting, or hard to reverse (PROMPT-SYS §16) — e.g. ratifications, authority grants, thresholds.
- **Home & numbering:** `Company/Decision-Records/WES-DEC-###.md`, sequential, never reused; a superseding decision references the record it replaces — never edit a settled record in place.
- **Required fields (per WES-DEC-001):** a metadata table (Decision ID, Date, Owner, Status), then `Decision Summary`, `Reason`, `Alternatives Considered`, `Final Decision`, `Impact`, `References`.
- A recorded decision is **not re-litigated** without a new superseding record (PROMPT-SYS §11, §16).

## 6. Update Discipline
- **Documentation is part of the change, not after it** — a change is not Done until its docs are updated (PROMPT-SYS §22; SOP-CODING §11).
- **INVENTORY status transitions:** `Not Started → Draft → Reviewed → Ratified`.
  - **Author / Committee** moves Not Started → Draft (on commit).
  - **Reviewer** moves Draft → Reviewed (on PR review).
  - **Founder** moves Reviewed → Ratified, recorded as a `WES-DEC-###` (ratification is Founder-only).
- Whoever changes a document updates its INVENTORY row in the same change.

## 7. Versioning
- Governed documents carry **semantic versions** (v1.0, v1.1, …); status moves **Draft → Approved / Ratified** (Blueprint Vol 09; PROMPT-SYS §16).
- **Archived, not deleted** — outdated content is archived, preserving history (Blueprint Vol 09; PROMPT-SYS §16).
- A new version supersedes the prior; for governed documents the change is recorded as a `WES-DEC-###`.

## 8. Outputs & Examples
**Outputs:** every documentation change produces the updated file(s) in their correct home, the INVENTORY row moved to the right status, and — for a governed change — a `WES-DEC-###`. On the record, in Git (PROMPT-SYS §18, §19).

**Examples (real):**
- **Decision Record format:** `Company/Decision-Records/WES-DEC-001.md` — metadata table + Decision Summary / Reason / Alternatives Considered / Final Decision / Impact / References.
- **Verbatim governed doc:** `Company/Operating-Instructions/FOUNDER-INTENT.md` — the Founder's words, AI formatting only (WES-DEC-003).
- **Phase register:** `Company/Operating-Instructions/INVENTORY.md` — documents table, decision records, deploy-hold policy, change history.
- **Clean ratified doc:** `PROMPT-SYS.md` §23 (Approval Status = Ratified); the Version-History changelog was removed on ratification — the doc stays clean, provenance lives in Git + WES-DEC-001."""

SOP_SEC = """## 1. Purpose & Scope
Defines how security is enforced during work inside WES — the procedures around the security principles the Constitution states. The principles live in **PROMPT-SYS §17** (Least privilege; No secrets in code; Validate input; Secure by default; Review for risk) and are **not restated** here. Scope: every change and every credential.

## 2. Applicability
Every role applies these procedures. The **Security Engineer owns the security gate** and clears security findings (PROMPT-SYS §7; SOP-REVIEW §2). **Major security decisions are Founder-only** (PROMPT-SYS §6, §17).

## 3. Secrets Handling
- **Environment variables only** — no secret in code (PROMPT-SYS §17). Config is read once at startup via `app/core/config.py` `Settings` (`env_prefix="WES_"`): e.g. `WES_JWT_SECRET`, `WES_SECRET_KEY`, `WES_DATABASE_URL`. The insecure defaults ("…change-in-production") **MUST be overridden in production**.
- **Encryption at rest:** provider credentials are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) via `app/core/secrets.py` (`encrypt`/`decrypt`), keyed from `WES_SECRET_KEY`; secrets are **masked** in all output (`mask_secret`, `"***"`).
- **On discovering a committed secret** — treat as an **incident** (§7): (1) stop; (2) **rotate** the credential immediately; (3) remove it from the active configuration and prevent reuse; (4) record the incident + a lesson. A secret in Git history is compromised — rotation, not deletion, is the fix.

## 4. Input & Dependency Validation
- **Validate at the API boundary** — every request/response is typed and validated by a Pydantic schema (`app/schemas/`); never trust external data (PROMPT-SYS §17).
- **Dependency addition procedure** (SOP-CODING §5): **justify → license check → security review**, in that order. A dependency is added only after all three pass; an unjustified dependency is rejected.

## 5. Security Review Procedure
- The **security gate** runs on every code change, as part of review (SOP-REVIEW §4).
- **Engine & checks** — `app/services/quality_review_engines.py` `SecurityReviewService` flags: secrets **CWE-798** (CRITICAL), SQL injection **CWE-89** (CRITICAL), command injection **CWE-78** (CRITICAL), eval/exec **CWE-95** (HIGH), path traversal **CWE-22** (MEDIUM). Each finding carries a `FindingSeverity`.
- **A finding triggers:** CRITICAL/HIGH **blocks** — the change cannot proceed until resolved.
- **Who may clear a finding:** the **Security Engineer** (the gate owner) — **never the author** (SOP-REVIEW §6, §10). Every clearance records its reason.

## 6. Access & Permissions
- **Least privilege** (PROMPT-SYS §17): request and hold only the access a task requires. Enforced by `app/domain/roles.py` (`Role`, `Permission`); Founder-only permissions include `repo:write`, `dev:approve`, `orch:write` (pipeline / provider settings), and `devops:production`.
- **GitHub App tokens:** short-lived installation tokens; the **private key never leaves the host and is never printed** (WES-DEC-002). The personal token is not used for writes.
- **Provider keys:** encrypted at rest, scoped to an environment profile (`app/models/provider_platform.py`); surfaced only masked (`providers_service.py`).
- **An agent may never request** production credentials, a standing broad token, or access beyond its task scope — it escalates instead (PROMPT-SYS §7, §15).

## 7. Incident Handling
- On any suspected breach, leak, or committed secret: **stop → contain → escalate** to the Studio Director → Founder (PROMPT-SYS §15, §17).
- Record an **`IncidentReport`** (`app/models/devops.py`; `IncidentSeverity`, `IncidentStatus` default `open`) with severity, containment, and resolution; capture a **lesson** in Company Memory (PROMPT-SYS §16).
- **Never hide or downplay an incident** — concealment is a truth violation (FOUNDER-INTENT §6; PROMPT-SYS §21).

## 8. Prohibited Actions (operational forms of PROMPT-SYS §17, §21)
- **Never disable, weaken, or bypass a security check** to make work pass.
- **Never route a test key, mock, or insecure default into a production path.**
- **Never commit a secret, log a secret in plaintext, or output an unmasked credential.**
- **Never assist in producing destructive, evasive, or unauthorized capabilities** (PROMPT-SYS §17).

## 9. Outputs & Examples
**Outputs:** security-review findings (with `FindingSeverity` + CWE), the gate verdict, any `IncidentReport` + lesson, and the recorded clearance / rotation — on the record (PROMPT-SYS §18, §19).

**Examples (real):**
- **Hardcoded-secret block:** `SecurityReviewService` flags a hardcoded secret as `FindingSeverity.CRITICAL` (CWE-798); the review cannot approve until the Security Engineer clears it (§5).
- **Encryption at rest:** `app/core/secrets.py` (Fernet + `mask_secret`); provider credentials stored encrypted (`app/models/provider_platform.py`), surfaced masked (`"***"`).
- **Token precedent:** WES-DEC-002 — PR/merge via a short-lived GitHub App installation token; the private key is never printed.
- **Founder-only config:** `orch:write` (provider settings) and `devops:production` require the Founder (`app/domain/roles.py`)."""


RATIFIED_SOPS: list[SOPSpec] = [
    SOPSpec('SOP-CODE', 'SOP-CODING', 'Coding SOP', SOPCategory.CODING, SOP_CODE),
    SOPSpec('SOP-REVIEW', 'SOP-REVIEW', 'Review SOP', SOPCategory.REVIEW, SOP_REVIEW),
    SOPSpec('SOP-TEST', 'SOP-TESTING', 'Testing SOP', SOPCategory.TESTING, SOP_TEST),
    SOPSpec('SOP-DEPLOY', 'SOP-DEPLOYMENT', 'Deployment SOP', SOPCategory.DEPLOYMENT, SOP_DEPLOY),
    SOPSpec('SOP-DOCS', 'SOP-DOCUMENTATION', 'Documentation SOP', SOPCategory.DOCUMENTATION, SOP_DOCS),
    SOPSpec('SOP-SEC', 'SOP-SECURITY', 'Security SOP', SOPCategory.SECURITY, SOP_SEC),
]
