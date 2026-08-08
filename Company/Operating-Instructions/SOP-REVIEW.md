# SOP-REVIEW — Standard Operating Procedure for Review

| Field | Detail |
|-------|--------|
| **Document ID** | SOP-REVIEW (doc 06 of 27) |
| **Author** | WES Engineering Standards Committee |
| **Status** | Ratified — `WES-DEC-005` (2026-08-04) |
| **Governance** | Procedure only. Subordinate to the Blueprint, `PROMPT-SYS`/`PROMPT-SYS-CORE`, `FOUNDER-INTENT`, `COMPANY-PHILOSOPHY`, and `SOP-CODING`. Where those state a rule, this SOP cites it and does not restate it. |
| **Authority order** | Blueprint → PROMPT-SYS / PROMPT-SYS-CORE → FOUNDER-INTENT → COMPANY-PHILOSOPHY → SOPs |
| **Version** | 1.0 — 2026-08-04 |

---

## 1. Purpose & Scope
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
- **Human-PR rejection:** No repository example exists yet — this program's PRs (#1–#3) were Founder-approved; the bar in §5 still applies.

## 12. Appendix — Referenced Documents
`PROMPT-SYS.md` §6/§7/§11/§15/§16/§18/§19/§22; `PROMPT-SYS-CORE.md`; `FOUNDER-INTENT.md` §6; `COMPANY-PHILOSOPHY.md` value 7; `SOP-CODING.md` §4/§5/§6/§7/§8/§9/§10/§11/§15; Blueprint Vol 04 (Code Review Process), Vol 08 (Code Review Policy); `app/services/quality_review_engines.py`; `app/services/autonomous_engineering.py`; `app/api/v1/execution.py` (`/reviews`); `app/domain/execution_enums.py` (`ReviewStatus`).

### Open Founder Decisions
- None open. Review roles, verdicts, engines, and board unanimity are all defined in the repository and cited above.
