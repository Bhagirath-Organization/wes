# SOP-DEPLOYMENT — Standard Operating Procedure for Deployment

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-DEPLOYMENT (doc 08 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Draft — Founder ratification pending |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, `SOP-CODING`, `SOP-TESTING`. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → SOPs |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & Scope
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
- **Founder-only endpoints:** `POST /devops/pipelines/{id}/deploy-production` and `POST /devops/rollback` require `devops:production` (Founder); `POST /devops/pipelines/run` requires `devops:execute` (Founder + Director).

## 11. Appendix — Referenced Documents
`PROMPT-SYS.md` §6/§9/§17/§18/§19/§20/§22; `PROMPT-SYS-CORE.md`; `COMPANY-PHILOSOPHY.md` value 7; `SOP-CODING.md` §6/§12; `SOP-TESTING.md` §5; `INVENTORY.md` (deploy-hold policy); Blueprint Vol 04 (Release Process), Vol 06 (Infrastructure), Vol 10 (Automation); `app/services/devops_pipeline.py` (`_STAGES`), `devops_build.py`, `devops_release.py`, `devops_deploy.py`, `devops_monitor.py`; `app/domain/devops_enums.py`; `app/models/devops.py`; `app/api/v1/devops.py`; `docker-compose.green.yml`; `deploy/vps/` (`bootstrap.sh`, `verify.sh`); `scripts/health.sh`.

### Open Founder Decisions
- None open. Environments, pipeline stages, gates, and rollback are defined in the repository and cited above. The **timing** of the combined end-of-phase production deploy is a standing Founder decision per the INVENTORY deploy-hold policy.
