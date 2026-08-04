# WES-DEC-004 — Ratcheting backend test-coverage floor

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-004 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved |

## Decision Summary
Establish a **ratcheting** backend test-coverage floor. Baseline measured **73%** line
coverage (12,042 / 16,512 statements) on 2026-08-04 via `coverage run --source=app -m pytest`.
Initial floor = baseline − 2% = **71%**.

## Reason
- Coverage must never regress silently (COMPANY-PHILOSOPHY value 7 — evidence over claims).
- A ratchet is earned, not arbitrary: the floor is derived from real measurement and only ever rises.

## Alternatives Considered
- **A fixed high target (e.g. 90%).** Rejected — arbitrary and could block delivery; not grounded in measurement.
- **No threshold.** Rejected — permits silent regression.

## Final Decision
- **Backend line-coverage floor = 71%** (effective 2026-08-04).
- **Ratchet rule:** whenever a newly measured baseline `B` exceeds `floor + 2`, the floor rises
  to `B − 2`. The floor **never decreases**.
- **Frontend floor: Deferred (by decision, not undefined).** The frontend suite has ~42 tests;
  measuring a baseline on a suite that small yields a meaningless number. The same ratchet will
  set the frontend floor once the suite matures — revisit at the **end of the Operating
  Instructions phase**.
- Measurement of record: coverage.py over `app/` (`[tool.coverage.run] source=["app"]`).

## Impact
- `SOP-CODING` §10 changes from "Not defined" to "backend line coverage ≥ 71% (ratchet)".
- **CI enforcement — approved as a separate engineering PR, after the Batch-2 docs PR merges.**
  Scope (kept deliberately small): add `pytest-cov` as a backend dev dependency and wire
  `--cov=app --cov-fail-under=71` into `scripts/test.sh` (which currently runs `pytest -q`
  without coverage). This is the docs phase's **first code-change exception**, so that PR must
  itself follow `SOP-CODING` end-to-end — feature branch → tests → PR → Founder merge — as the
  **SOP's first real execution**.
- **Measurement caveat:** baseline taken in the keyless CI environment where one environment-only
  test (`test_execute_dry_run_is_side_effect_free`, GitHub App not configured) fails; that path is
  a small, conservative under-count. No production impact; deploy remains held.

## References
- `Company/Operating-Instructions/SOP-CODING.md` §10; `backend/pyproject.toml`
- Related: [[WES-DEC-001]]
