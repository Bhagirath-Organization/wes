# SOP-TESTING — Standard Operating Procedure for Testing

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-TESTING (doc 07 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Ratified — `WES-DEC-005` (2026-08-04) |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, `SOP-CODING`, `SOP-REVIEW`. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → SOPs |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & Scope
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
- **Observed baseline:** full suite = **461 collected, 460 passed, 1 (environment-only) failed**; coverage **73%** (`coverage run --source=app -m pytest`).

## 11. Appendix — Referenced Documents
`PROMPT-SYS.md` §7/§15/§20/§21; `PROMPT-SYS-CORE.md` (FAILURE); `FOUNDER-INTENT.md` §6; `COMPANY-PHILOSOPHY.md` value 7; `SOP-CODING.md` §2/§10; `SOP-REVIEW.md` §2/§3; `WES-DEC-004` (coverage ratchet); Blueprint Vol 08 (Testing Strategy); `scripts/test.sh`; `backend/tests/conftest.py`; `backend/pyproject.toml`; `frontend/vite.config.ts`, `frontend/vitest.setup.ts`.

### Open Founder Decisions
- **Frontend coverage floor** — Deferred per WES-DEC-004 (ratchet after the frontend suite matures; revisit at the end of the Operating Instructions phase).
- **CI enforcement of the coverage floor** — **live** via `scripts/test.sh --cov-fail-under=71` (WES-DEC-004).
