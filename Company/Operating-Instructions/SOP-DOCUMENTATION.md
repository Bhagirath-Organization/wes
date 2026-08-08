# SOP-DOCUMENTATION — Standard Operating Procedure for Documentation

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-DOCUMENTATION (doc 09 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Ratified — `WES-DEC-005` (2026-08-04) |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, and the other SOPs. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → SOPs |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & Scope
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
- **Clean ratified doc:** `PROMPT-SYS.md` §23 (Approval Status = Ratified); the Version-History changelog was removed on ratification — the doc stays clean, provenance lives in Git + WES-DEC-001.

## 9. Appendix — Referenced Documents
`PROMPT-SYS.md` §7/§11/§14/§16/§18/§19/§21/§22; `PROMPT-SYS-CORE.md`; `FOUNDER-INTENT.md`; `COMPANY-PHILOSOPHY.md`; `SOP-CODING.md` §11; Blueprint Vol 09 (Knowledge Management), Vol 03 (Technical Writer); `Company/Decision-Records/` (WES-DEC-001…004); `Company/Operating-Instructions/INVENTORY.md`; `Employees/<Role>/README.md`; `docs/`.

### Open Founder Decisions
- None open. Document homes, formats, INVENTORY transitions, and versioning are defined in the repository and cited above.
