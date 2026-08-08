# WES-DEC-009 — Mission budget enforcement: per-run cap supersedes "all limits $5"

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-009 |
| **Date** | 2026-08-07 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved |

## Decision Summary
For the TEST-MISSION-CHARTER live run, the budget enforcement is **`max_cost = $5.00 per execution`
plus `hard_stop = true`** on the global `BudgetConfig`. The period limits remain the Founder's
pre-existing live-use configuration — `daily_cost_limit = $50`, `monthly_cost_limit = $1000` — and
are **not** lowered to $5.

## Reason
- The green environment was already in live use before the mission; its daily/monthly limits are
  the Founder's working configuration for that ongoing usage, not mission parameters.
- The charter's protection intent — no runaway mission spend — is fully carried by the per-run
  $5 hard cap with `hard_stop`, which the budget gate checks **before any provider is contacted**
  (`BudgetService.check`; verified live: the gated ping and all five mission runs).

## Alternatives Considered
- **Set all limits to $5 (charter §3 as written).** Rejected — it would throttle the Founder's
  pre-existing live usage of the same environment for no additional mission safety.
- **Separate mission-scoped budget config.** Deferred — `BudgetConfig` is global-scope today;
  a scoped budget is an engineering change out of the mission's observation scope.

## Final Decision
Mission cap = **$5.00 per execution + hard_stop**, effective 2026-08-07. This **supersedes
TEST-MISSION-CHARTER §3's "all limits $5"** for the live run. Actual recorded mission spend:
**$0.0855** (gated ping + five task executions) — 1.7% of a single run's cap.

## Impact
- Charter finding **F4 closed** by Founder decision; the mission proceeded under this enforcement.
- The known accounting gap stands separately (finding **F6**): executive-reasoning/planning calls
  do not record `provider_usage`; fixing that metering is a queued post-mission engineering item.

## References
- `Company/Operating-Instructions/TEST-MISSION-CHARTER.md` §3/§8; `backend/app/services/budget_service.py`
- Related: [[WES-DEC-010]]
