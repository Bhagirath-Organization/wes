"""Autonomous Software Engineering (Phase 5).

Adds the senior-engineer behaviours the dev workflow was missing, built ON TOP of
the existing engine (``development_service`` / ``dev_generation`` / ``dev_review``
/ ``dev_git`` / quality gate) — nothing is rebuilt:

* ``engineering_context`` — repository-aware + memory-aware context so generated
  code reuses existing modules/conventions instead of duplicating them.
* ``self_debug`` — real fix loop: on test failure, do root-cause analysis, generate
  a targeted fix, re-apply and re-test; never stop after the first failure.
* ``review_board`` — four independent senior reviewers (Chief Architect, QA,
  Security, Performance) each reason over the ACTUAL diff and may block.
* ``merge_readiness`` — aggregate gate over tests + board into a mergeable verdict.

Every judgement is a real provider call (reuses the Phase 1 reasoning plumbing);
none is scripted, so different code produces different reviews.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

_FILE_RE = re.compile(
    r"<<<FILE:\s*(?P<path>.+?)>>+[ \t]*\n(?P<body>.*?)(?:\n<<<END>>+|\Z)", re.DOTALL
)


def _s(v, n=1500):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


def _slist(v, n=10):
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    return [str(x).strip()[:300] for x in v if str(x).strip()][:n]


class AutonomousEngineeringService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.executive_reasoning import ExecutiveReasoningService

        self._exec = ExecutiveReasoningService(db)

    # -- repository- & memory-aware context --------------------------------

    def engineering_context(self, title: str, description: str | None = None) -> str:
        """What already exists (repo) + what we've learned (memory), for the coder."""
        bits: list[str] = []
        # Repository intelligence (reuse Phase 2 module/layer analysis).
        try:
            from app.models.repository import Repository
            from app.services.repo_analysis import ArchitectureService

            repo = self.db.scalar(select(Repository).limit(1))
            if repo is not None:
                arch = ArchitectureService(self.db)
                mods = [m.get("name") for m in arch.modules(repo.id)][:25]
                layers = [l.get("layer") or l.get("name") for l in arch.layers(repo.id)][:12]
                if mods:
                    bits.append("Existing modules (REUSE, do NOT duplicate): " + ", ".join(filter(None, mods)))
                if layers:
                    bits.append("Architecture layers (stay consistent): " + ", ".join(filter(None, layers)))
        except Exception:
            pass
        # Company memory recall (reuse Phase 4 semantic recall).
        try:
            from app.services.company_memory import CompanyMemoryService

            ctx = CompanyMemoryService(self.db).planning_context(f"{title} {description or ''}")
            if ctx:
                bits.append(ctx)
        except Exception:
            pass
        return "\n".join(bits)

    # -- self-debugging loop -----------------------------------------------

    def self_debug(
        self, *, task, sandbox: str, git, changes, provider_name: str | None = None,
        max_iterations: int = 2,
    ) -> dict:
        """Fail -> root-cause -> fix -> retest, until green or blocked.

        Returns a structured record of every iteration (evidence, not a claim).
        Never fabricates success: the final ``resolved`` reflects the real test run.
        """
        from app.services.dev_review import TestingService

        py_files = [c.path for c in changes if c.language == "python"]
        iterations = []
        resolved = True
        for i in range(max_iterations + 1):
            runs = TestingService(self.db).run(task.id, sandbox, py_files)
            failed = sum(r.failed_count for r in runs)
            passed = sum(r.passed_count for r in runs)
            failing_output = "\n".join(
                r.output for r in runs if (r.failed_count or 0) > 0 or (r.status not in ("passed", "skipped"))
            )
            if failed == 0 and all(r.status in ("passed", "skipped") for r in runs):
                iterations.append({"iteration": i, "passed": passed, "failed": failed, "action": "green"})
                resolved = True
                break
            resolved = False
            if i >= max_iterations:
                iterations.append({"iteration": i, "passed": passed, "failed": failed, "action": "blocked"})
                break
            # Root-cause analysis + fix (real reasoning over the real failure).
            fix = self._diagnose_and_fix(task, git, failing_output, py_files, provider_name)
            if not fix.get("applied"):
                iterations.append(
                    {"iteration": i, "passed": passed, "failed": failed,
                     "action": "no_fix", "root_cause": fix.get("root_cause")}
                )
                break
            iterations.append(
                {"iteration": i, "passed": passed, "failed": failed, "action": "fixed",
                 "root_cause": fix.get("root_cause"), "files_fixed": fix.get("files")}
            )
        return {"resolved": resolved, "iterations": iterations}

    def _diagnose_and_fix(self, task, git, failing_output, py_files, provider_name) -> dict:
        current = {p: (git.read_file(p) or "") for p in py_files}
        listing = "\n\n".join(f"<<<FILE: {p}>>>\n{c}\n<<<END>>>" for p, c in current.items())
        emp = self._exec._employee_for_role("BACKEND_ENGINEER", "CHIEF_ARCHITECT")
        try:
            data = self._exec._reason(
                "AI Backend Engineer (debug)", emp,
                "You are debugging failing tests. Identify the ROOT CAUSE, then output the "
                "corrected FULL content of ONLY the files that must change. Reply with ONLY JSON: "
                '{"root_cause":"...","files":[{"path":"...","content":"...corrected full file..."}]}',
                f"Task: {task.title}\nFailing test output:\n{failing_output[:2500]}\n\n"
                f"Current files:\n{listing[:4000]}",
            )
        except Exception as exc:
            return {"applied": False, "root_cause": f"diagnosis failed: {exc}"}
        applied = []
        for f in (data.get("files") or [])[:6]:
            if not isinstance(f, dict):
                continue
            path = _s(f.get("path"), 200).lstrip("/")
            content = f.get("content")
            if path and isinstance(content, str) and content.strip():
                git.write_file(path, content)
                applied.append(path)
        if applied:
            git.stage_all()
            git.commit(f"fix: address failing tests for {task.title}"[:100])
        return {"applied": bool(applied), "root_cause": _s(data.get("root_cause"), 600), "files": applied}

    # -- senior review board -----------------------------------------------

    _REVIEWERS = (
        ("AI Chief Architect", ("CHIEF_ARCHITECT", "CTO"), "architecture consistency, maintainability and scalability"),
        ("AI QA Engineer", ("QA_ENGINEER",), "correctness, test coverage and business correctness"),
        ("AI Security Engineer", ("SECURITY_ENGINEER",), "security vulnerabilities, secrets and input validation"),
        ("AI Performance Reviewer", ("DEVOPS_ENGINEER", "BACKEND_ENGINEER"), "performance, efficiency and resource use"),
    )

    def review_board(self, task, diff: str) -> dict:
        """Four senior reviewers reason over the real diff; each may block.

        Company Brain (Phase A): every reviewer reasons WITH company intelligence —
        the Blueprint (the standards they enforce) and known mistakes to avoid — so
        review is Blueprint- and history-aware, not just diff-local.
        """
        from app.services.company_brain import CompanyBrain

        brain = CompanyBrain(self.db)
        intel = brain.intelligence(task.title)
        intel_text = brain.intel_text(intel)
        reviews = []
        for label, codes, lens in self._REVIEWERS:
            emp = self._exec._employee_for_role(*codes)
            try:
                data = self._exec._reason(
                    label, emp,
                    f"You are the {label} reviewing a code change for {lens}. Enforce the "
                    "company Blueprint and avoid repeating known mistakes (provided below). "
                    "You have authority to BLOCK. Do not rubber-stamp. Reply with ONLY JSON: "
                    '{"verdict":"approved|changes_requested","score":0,"findings":["..."],'
                    '"required_changes":["..."]}',
                    f"Task: {task.title}\n\nCOMPANY INTELLIGENCE:\n{intel_text}\n\n"
                    f"Diff:\n{diff[:3500]}",
                )
            except Exception as exc:
                data = {"verdict": "changes_requested", "score": 0,
                        "findings": [f"review failed: {exc}"], "required_changes": []}
            try:
                score = int(float(data.get("score") or 0))
            except (TypeError, ValueError):
                score = 0
            reviews.append(
                {
                    "reviewer": label,
                    "role": self._role_title(emp),
                    "dimension": lens.split(",")[0],
                    "verdict": _s(data.get("verdict"), 30).lower() or "approved",
                    "score": max(0, min(score, 100)),
                    "findings": _slist(data.get("findings")),
                    "required_changes": _slist(data.get("required_changes")),
                }
            )
        approved = all(r["verdict"] == "approved" for r in reviews)
        return {
            "approved": approved,
            "reviews": reviews,
            "blocking": [r["reviewer"] for r in reviews if r["verdict"] != "approved"],
        }

    def _role_title(self, emp):
        from app.models.ai import AIRole

        if not emp or not emp.role_id:
            return None
        role = self.db.get(AIRole, emp.role_id)
        return role.title if role else None

    # -- merge readiness ---------------------------------------------------

    @staticmethod
    def merge_readiness(*, tests_passed: bool, gate_eligible: bool, board: dict,
                        requirements_ok: bool = True) -> dict:
        """Aggregate all engineering gates into a single mergeable verdict."""
        blockers = []
        if not tests_passed:
            blockers.append("tests failing")
        if not gate_eligible:
            blockers.append("quality gate not eligible")
        if not board.get("approved"):
            blockers.extend(f"{r} requested changes" for r in board.get("blocking", []))
        if not requirements_ok:
            blockers.append("requirements not satisfied")
        return {
            "merge_ready": not blockers,
            "blockers": blockers,
            "gates": {
                "tests_passed": tests_passed,
                "quality_gate_eligible": gate_eligible,
                "review_board_approved": board.get("approved", False),
                "requirements_satisfied": requirements_ok,
            },
        }
