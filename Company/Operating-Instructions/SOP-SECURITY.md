# SOP-SECURITY — Standard Operating Procedure for Security

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-SECURITY (doc 10 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Draft — Founder ratification pending |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, and the other SOPs. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → SOPs |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & Scope
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
- **Founder-only config:** `orch:write` (provider settings) and `devops:production` require the Founder (`app/domain/roles.py`).

## 10. Appendix — Referenced Documents
`PROMPT-SYS.md` §6/§7/§15/§16/§17/§18/§19/§21; `PROMPT-SYS-CORE.md`; `FOUNDER-INTENT.md` §6; `SOP-CODING.md` §5/§9; `SOP-REVIEW.md` §4/§6/§10; `WES-DEC-002` (App token); Blueprint Vol 08 (Security Standards); `app/core/config.py`; `app/core/secrets.py`; `app/services/quality_review_engines.py` (`SecurityReviewService`); `app/models/provider_platform.py`; `app/services/providers_service.py`; `app/domain/roles.py`; `app/models/devops.py` (`IncidentReport`); `app/schemas/`.

### Open Founder Decisions
- None open. Secrets handling, validation, the security gate, permissions, and incident handling are defined in the repository and cited above.
