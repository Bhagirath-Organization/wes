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
| 03–27 | — | (pending) | — | Not started | — |

## Decision Records

| ID | Summary | Date | Location |
|----|---------|------|----------|
| `WES-DEC-001` | Ratification of PROMPT-SYS v1.1 & PROMPT-SYS-CORE v1.0 by the Founder | 2026-08-04 | `Company/Decision-Records/WES-DEC-001.md` |
| `WES-DEC-002` | Agent may create PRs and execute Founder-instructed merges via the GitHub App; merge decision stays Founder-only | 2026-08-04 | `Company/Decision-Records/WES-DEC-002.md` |

## Code / integration changes

| Change | PR | Merge | Deployed? |
|--------|----|-------|-----------|
| Seed `PROMPT-SYS` v2 (PROMPT-SYS-CORE) + idempotent `sync_prompt_sys()` in-place upsert | **#1** | **Merged (squash)** `9945792` on 2026-08-04 | **NO — held for combined final deploy** |
| Batch-0 close: commit ratified `PROMPT-SYS.md`, `WES-DEC-001/002`, this INVENTORY | **docs/batch-0-close** (PR open) | pending | **NO — docs only, no deploy** |

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

## Change history

| Date | Entry |
|------|-------|
| 2026-08-04 | Doc 01 `PROMPT-SYS` v1.1 authored (constitutional freeze review). Doc 02 `PROMPT-SYS-CORE` v1.0 authored, seeded as `PROMPT-SYS` v2, verified, **PR #1 merged to `main`** (`9945792`). Deploy **held** for combined final deploy. |
| 2026-08-04 | **Batch-0 close:** Founder **ratified** PROMPT-SYS v1.1 + CORE v1.0 (`WES-DEC-001`); agent PR/merge authority recorded (`WES-DEC-002`); ratified `PROMPT-SYS.md` committed; docs 01–02 marked **Ratified**. Branch `docs/batch-0-close` (PR open). |
