# WES-DEC-012 — Combined production deploy: the hold is lifted

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-012 |
| **Date** | 2026-08-08 |
| **Owner** | Founder / Owner (Human) |
| **Status** | DRAFT — awaiting Founder approval; deploy executes only on the Founder's explicit go |

## 1. What deploys
The **entire merged backlog of `main` — PR #1 through PR #16** — held since the Operating
Instructions phase began (INVENTORY deploy policy):
`PROMPT-SYS` v2 seed + `sync_prompt_sys` (#1) · ratified Constitution + decision records (#2) ·
governed strategy docs (#3) · SOP Library docs (#4) · coverage CI (#5) · role prompts (#6) ·
shared activity prompts (#7) · TEST-MISSION-CHARTER (#8) · **Prompt Library seed** (#9) ·
**Knowledge Engine load** (#10) · **budget-gated provider ping** (#11) · post-mission
reconciliation (#12) · **governed `truncate()`** (#13) · **F9 governance injection** (#14) ·
**F6 reasoning-path metering** (#15) · **ratified SOP library + WES-DEC-011** (#16).
One combined deploy, as the phase policy promised.

## 2. Evidence base (all verified this phase, records in INVENTORY)
- **§6.1 PASS** — mission run #2's composed prompt carried Constitution + Role Prompt +
  PROMPT-TASK **byte-verbatim** from the seeded libraries (run `dbf275a6`, thread `96e02caa`);
  hand-rolled personas retired; `prompt_version v2`.
- **F6 closed** — both spend circuits metered: orchestration pipeline AND the
  reasoning/dev-gen/consensus path record `ProviderUsage` via `CostEngine` (PR #15).
- **Frontend byte-current** — the running bundle equals HEAD source (0 newer files); **218/218**
  frontend-referenced endpoints exist live with matching verbs; proxy healthy.
- **Test evidence** — full backend suite **572 passed, coverage 73.52%** (floor 71,
  WES-DEC-004); the single failing test is the known env-only ATLAS item (untracked file,
  GitHub-key precondition — green carries the key).
- **Findings ledger F1–F12** — every mission finding is **fixed** (F1/F2/F3-part/F4/F6/F9,
  sop-stubs) **or formally decided/queued** (F5, F7, F8, F10, F11, envelope WES-DEC-011,
  seed_ai reconciliation).

## 3. Effect of this decision
On Founder approval of this record **the phase deploy-hold is officially LIFTED**. From this
deploy onward, releases follow **SOP-DEPLOYMENT's normal regime** — no standing hold; production
deploys remain Founder-gated per `devops:production` and PROMPT-SYS §6, per release.

## 4. Rollback readiness (SOP-DEPLOYMENT §7)
The rollback path is confirmed available before execution: previous known-good backend image
retained (current production image is untouched until the deploy); DB changes are additive only
(no destructive migration in #1–#16; the idempotent `sync_*` upserts modify seeded content in
place and are re-runnable); rollback = redeploy prior image (`POST /devops/rollback` /
docker-compose with the retained tag) + no schema down-migration required. Founder-only.

## 5. Execution plan (SOP-DEPLOYMENT §4–§6 — runs ONLY after the Founder's explicit go)
1. **Pipeline** — build production backend image from `main` (`4f0da94`), tag + retain the prior
   image for rollback.
2. **Deploy** to the production target; run migrations (additive only; alembic no-ops where
   current); run the idempotent seed (`sync_prompt_sys` + `sync_prompt_library` +
   `sync_knowledge_library` + `sync_sop_library` — in-place, no destructive re-seed).
3. **Health verification** — `health.sh` **exit 0** required; `GET /api/v1/health` 200.
4. **Specific-change verification** —
   a. `PROMPT-SYS` **v2** visible in the live `/execution` Prompt Library (the check promised in
      INVENTORY's deploy policy since PR #1), 18 templates present, 6 ratified SOP bodies present;
   b. **one composed-prompt sample** on the production stack (mock or minimal governed call, at
      the Founder's discretion) showing CORE + ROLE + TASK + ratified SOP — the §6.1 shape.
5. **Report** — 5-part deploy report with evidence; any failed gate → STOP + rollback per §7,
   report honestly (a failed deploy with evidence is a valid outcome).

## Reason
The phase's purpose is complete: 27 ratified documents, proven live injection, a metered money
path, and a mission-tested workflow. Holding longer adds risk (drift between main and
production), not safety.

## Alternatives Considered
- **Continue the hold.** Rejected — the evidence base above is the strongest the phase can
  produce without deploying.
- **Partial deploy (docs/seeds only).** Rejected — splits a tested `main` into an untested
  combination; the hold's entire premise was one combined, coherent release.

## Impact
- Production gains: governed prompts live, ratified libraries seeded, metering on both circuits,
  ping endpoint, `truncate()`.
- Post-deploy queue (in order, per WES-DEC-011 and the roadmap): **Mission Budget Envelope
  implementation** (first PR, before F10) → F10 (execution→PR bridge) → F11 (inter-task handoff)
  → seed_ai reconciliation WES-DEC (incl. AI CEO / AI CTO role-prompt mapping).

## References
- INVENTORY (deploy policy, findings ledger, PR table #1–#16); [[WES-DEC-009]], [[WES-DEC-010]],
  [[WES-DEC-011]]; `SOP-DEPLOYMENT.md` §4–§7; mission runs `2e2cae92…274c9a1a`, `dbf275a6`.
