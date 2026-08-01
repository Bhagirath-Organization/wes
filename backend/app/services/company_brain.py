"""Company Brain — the central reasoning layer (Phase A).

Every executive decision inside WES passes through the Company Brain. The Brain
does NOT re-implement reasoning, memory, repository analysis, or the Blueprint —
it ORCHESTRATES the systems that already exist and turns their combined signal
into a single, structured, evidence-based deliberation:

    intelligence()  — gather (no LLM): company memory + similar projects + past
                      mistakes (learning rules) + repository intelligence
                      (modules/layers/dependencies) + Blueprint references.
    deliberate()    — reason (one LLM call, reusing ExecutiveReasoningService's
                      provider plumbing) with a role-specific lens, producing:
                      business / technical / blueprint / repository justification,
                      risks, ALTERNATIVES, a recommendation, and a confidence score.

Reused, never duplicated: ExecutiveReasoningService (provider + JSON plumbing),
CompanyMemoryService (semantic recall + learning), ArchitectureService /
DependencyService (repository intelligence), and the Blueprint volumes on disk.
"""

from __future__ import annotations

import os
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

# Where the Blueprint is mounted read-only inside the container (the Constitution).
_BLUEPRINT_DIR = os.environ.get("WES_BLUEPRINT_DIR", "/app/Blueprint")

# The structured reasoning contract every deliberation must satisfy. Kept as one
# string so the executive prompts and the Brain request the SAME schema.
REASONING_SCHEMA = (
    '{"recommendation":"...",'
    '"business_justification":"...",'
    '"technical_justification":"...",'
    '"blueprint_justification":"...",'
    '"repository_justification":"...",'
    '"risks":["..."],'
    '"alternatives":["..."],'
    '"confidence":0.0}'
)

# Per-executive reasoning lens — each executive thinks about different things
# (Blueprint Vol 03 role purposes). This is the ONLY per-role divergence; the
# output contract is shared so decisions are comparable.
_LENS = {
    "CEO": ("AI CEO", ("CEO",),
            "business viability, ROI, market and business risk, product vision, the "
            "customer, and growth"),
    "CTO": ("AI CTO", ("CTO", "CHIEF_ARCHITECT"),
            "technology choices, scalability, integration, maintainability, and the "
            "overall system architecture"),
    "CHIEF_ARCHITECT": ("AI Chief Architect", ("CHIEF_ARCHITECT", "CTO"),
            "structure, proven software patterns, REUSE of what already exists, "
            "dependencies, and technical debt"),
    "SECURITY": ("AI Security Engineer", ("SECURITY_ENGINEER",),
            "security threats, compliance, privacy, and secure-by-default design"),
    "QA": ("AI QA Engineer", ("QA_ENGINEER",),
            "verification, acceptance criteria, regression risk, and performance"),
}


def _clip(v, n=600):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


def _as_list(v, n=8):
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    return [str(x).strip()[:300] for x in v if str(x).strip()][:n]


class CompanyBrain:
    _blueprint_cache: dict | None = None

    def __init__(self, db: Session):
        self.db = db
        from app.services.executive_reasoning import ExecutiveReasoningService

        self._exec = ExecutiveReasoningService(db)  # reuse provider + JSON plumbing

    # ------------------------------------------------------------------ #
    #  Blueprint Intelligence (the Constitution)                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def _blueprint_index(cls) -> dict:
        """Volume-title + governing-topics index, read once from the Blueprint."""
        if cls._blueprint_cache is not None:
            return cls._blueprint_cache
        index: dict[str, str] = {}
        try:
            for name in sorted(os.listdir(_BLUEPRINT_DIR)):
                vol = os.path.join(_BLUEPRINT_DIR, name)
                readme = os.path.join(vol, "README.md")
                if not os.path.isfile(readme):
                    continue
                with open(readme, "r", encoding="utf-8") as fh:
                    text = fh.read()
                title = name
                for line in text.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                # governing topics = the '## ' section headings
                topics = [ln[3:].strip() for ln in text.splitlines() if ln.startswith("## ")]
                index[title] = ", ".join(topics[:10])
        except FileNotFoundError:
            pass
        cls._blueprint_cache = index
        return index

    def blueprint_refs(self, objective: str, *, k: int = 3) -> list[str]:
        """Blueprint volumes most relevant to this objective (keyword overlap)."""
        index = self._blueprint_index()
        if not index:
            return []
        words = {w for w in objective.lower().split() if len(w) > 3}
        scored = []
        for title, topics in index.items():
            hay = f"{title} {topics}".lower()
            score = sum(1 for w in words if w in hay)
            # Volumes 04/05/08 are always constitutionally relevant to delivery.
            if any(v in title for v in ("Engineering System", "AI System", "Security")):
                score += 1
            scored.append((score, f"{title} — {topics}"))
        scored.sort(key=lambda s: -s[0])
        return [ref for _, ref in scored[:k]]

    # ------------------------------------------------------------------ #
    #  Repository Intelligence (never duplicate existing code)           #
    # ------------------------------------------------------------------ #

    def repository_intelligence(self) -> dict:
        """Existing modules / layers / dependencies, reusing the repo analyzers."""
        out: dict = {"modules": [], "layers": [], "dependency_hotspots": []}
        try:
            from app.models.repository import Repository
            from app.services.repo_analysis import ArchitectureService, DependencyService

            repo = self.db.scalar(select(Repository).limit(1))
            if repo is None:
                return out
            arch = ArchitectureService(self.db)
            out["modules"] = [m.get("name") for m in arch.modules(repo.id)][:30]
            out["layers"] = [l.get("layer") or l.get("name") for l in arch.layers(repo.id)][:12]
            try:
                dep = DependencyService(self.db)
                hotspots = getattr(dep, "hotspots", None)
                if callable(hotspots):
                    out["dependency_hotspots"] = [h.get("name") for h in hotspots(repo.id)][:10]
            except Exception:
                pass
        except Exception:
            pass
        return out

    # ------------------------------------------------------------------ #
    #  Intelligence gathering (NO LLM — pure assembly of what exists)    #
    # ------------------------------------------------------------------ #

    def intelligence(self, objective: str, *, project_id: uuid.UUID | None = None,
                     task: str | None = None) -> dict:
        """Everything the company already knows that bears on this objective.

        Reuses CompanyMemoryService (semantic recall + learning rules) and the
        repository analyzers. Cheap, deterministic, and safe when memory is empty.
        """
        recall = {"reuse": [], "avoid": []}
        try:
            from app.services.company_memory import CompanyMemoryService

            recall = CompanyMemoryService(self.db).recall_for_planning(
                f"{objective} {task or ''}", exclude_project=project_id
            )
        except Exception:
            pass
        repo = self.repository_intelligence()
        return {
            "similar_projects": [
                {"summary": _clip(r.get("summary"), 200), "similarity": round(r.get("similarity", 0), 2)}
                for r in (recall.get("reuse") or [])[:5]
            ],
            "avoid_mistakes": [_clip(r.get("rule") or r.get("summary"), 200)
                               for r in (recall.get("avoid") or [])[:5]],
            "repository": repo,
            "blueprint": self.blueprint_refs(objective),
        }

    def intel_text(self, intel: dict) -> str:
        """Render gathered intelligence for injection into an executive prompt."""
        parts: list[str] = []
        if intel.get("blueprint"):
            parts.append("BLUEPRINT (the Constitution — comply and cite):\n- "
                         + "\n- ".join(intel["blueprint"]))
        if intel.get("similar_projects"):
            parts.append("SIMILAR PAST PROJECTS (reuse, do not redo):\n- "
                         + "\n- ".join(f"{p['summary']} (sim {p['similarity']})"
                                       for p in intel["similar_projects"]))
        if intel.get("avoid_mistakes"):
            parts.append("KNOWN MISTAKES TO AVOID (company learning):\n- "
                         + "\n- ".join(intel["avoid_mistakes"]))
        repo = intel.get("repository") or {}
        if repo.get("modules"):
            parts.append("EXISTING REPOSITORY MODULES (REUSE, never duplicate):\n"
                         + ", ".join(filter(None, repo["modules"])))
        if repo.get("layers"):
            parts.append("ARCHITECTURE LAYERS (stay consistent):\n"
                         + ", ".join(filter(None, repo["layers"])))
        return "\n\n".join(parts)

    # ------------------------------------------------------------------ #
    #  Deliberation (one LLM call, structured, evidence-based)           #
    # ------------------------------------------------------------------ #

    def deliberate(self, role: str, objective: str, *, project_id: uuid.UUID | None = None,
                   question: str = "", intel: dict | None = None) -> dict:
        """A single executive's structured reasoning, grounded in company intelligence.

        Returns business/technical/blueprint/repository justification, risks,
        ALTERNATIVES, recommendation, and confidence. Reuses the executive provider
        plumbing (``_reason``) — no new provider path, no templated output.
        """
        label, codes, lens = _LENS.get(role.upper(), _LENS["CEO"])
        intel = intel if intel is not None else self.intelligence(objective, project_id=project_id)
        emp = self._exec._employee_for_role(*codes)
        instruction = (
            f"You are the {label} of an AI software company. Reason specifically about "
            f"{lens}. You MUST ground your reasoning in the company intelligence provided "
            "(Blueprint references, similar past projects, mistakes to avoid, and existing "
            "repository modules to REUSE). Consider at least two ALTERNATIVES before "
            "recommending. Reply with ONLY this JSON object, no prose:\n" + REASONING_SCHEMA
        )
        prompt = (
            f"Business objective: {objective}\n\n"
            f"COMPANY INTELLIGENCE:\n{self.intel_text(intel)}\n\n"
            f"{question}".strip()
        )
        data = self._exec._reason(label, emp, instruction, prompt)
        return self.normalize(data, role=role, intel=intel, analyst=(emp.name if emp else label))

    @staticmethod
    def normalize(data: dict, *, role: str, intel: dict, analyst: str) -> dict:
        """Coerce a deliberation into the fixed reasoning contract."""
        try:
            conf = float(data.get("confidence") or 0)
        except (TypeError, ValueError):
            conf = 0.0
        return {
            "role": role,
            "analyst": analyst,
            "recommendation": _clip(data.get("recommendation"), 800),
            "business_justification": _clip(data.get("business_justification"), 800),
            "technical_justification": _clip(data.get("technical_justification"), 800),
            "blueprint_justification": _clip(data.get("blueprint_justification"), 600),
            "repository_justification": _clip(data.get("repository_justification"), 600),
            "risks": _as_list(data.get("risks")),
            "alternatives": _as_list(data.get("alternatives")),
            "confidence": max(0.0, min(conf, 1.0)),
            "blueprint_refs": intel.get("blueprint", []),
            "reused_modules": (intel.get("repository") or {}).get("modules", [])[:10],
        }
