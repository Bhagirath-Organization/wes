# WES-DEC-011 — Mission Budget Envelope (supersedes per-call gating)

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-011 |
| **Date** | 2026-08-08 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved (design + decision; implementation scheduled) |

## Decision Summary
WES will not accumulate per-call / per-stage budget gates. Budget control moves to a
**Mission Budget Envelope**: one estimate, one Founder approval, free execution inside the
envelope, notification at 80%, hard-stop + escalation at 100%. This **supersedes** both the
open "reasoning-path pre-call gate" question (flagged in PR #15) and the **per-run `max_cost`
model, which is retired as a test-era stopgap** once the envelope is implemented.

## The model (Founder design, 2026-08-08)
1. **Estimate at intake.** On objective submission the system itself produces a cost estimate:
   planned tasks × real governed-call baselines (**~$0.027/governed call**, measured in mission
   run #2) **+ reasoning overhead + buffer**.
2. **One approval.** The estimate rides with the objective and plan in a **single Founder
   approval**: *"this objective, this plan, estimated $X — approve?"* No separate budget dialog.
3. **Free run inside the envelope.** Within the approved envelope, **all paths — executive
   reasoning and orchestration alike — run without further prompts.** The meter keeps running
   (F6 metering, PR #15); the Founder is not asked again.
4. **80% → notification** to the Founder.
5. **100% → hard-stop + `PROMPT-ESC` escalation** (the six-field package), mission paused.

## Reason
- Per-call gates multiply friction without adding safety once metering is trustworthy; the
  envelope puts the Founder decision where it belongs — at intake, with the plan, once.
- Run #2 gave a real per-call baseline; estimates can now be grounded, not guessed.

## Alternatives Considered
- **Add a reasoning-path pre-call gate (mirror of `run_stage`/ping).** Rejected — starts the
  per-call-gate pile-up this decision exists to prevent.
- **Keep per-run `max_cost` alongside the envelope.** Rejected — redundant once the envelope
  hard-stops at 100%; retained only until the envelope ships.

## Final Decision
The Mission Budget Envelope model is **approved as designed above**. **Implementation is the
first post-deploy scoped engineering PR, before F10.** No code changes ride with this record.
Until it ships, current protections stay: per-run `max_cost=$5` + `hard_stop` (WES-DEC-009)
plus full metering (PR #15).

## Impact
- PR #15's flagged open question is **closed by supersession**.
- Estimation needs plan-task counts × baselines — inputs that already exist (plan artifacts;
  `provider_usage` baselines). Envelope state (approved amount, spent, 80/100 triggers) will need
  a small schema addition — scoped to the implementation PR.
- `PROMPT-ESC` (doc 26) becomes the 100% escalation vehicle — its first wired consumer.

## References
- Mission run #2 baseline: run `dbf275a6` ($0.027423); [[WES-DEC-009]] (interim cap), PR #15 (F6
  metering), `Company/Operating-Instructions/PROMPT-ESC.md`, `INVENTORY.md`.
