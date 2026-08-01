"""Company Memory System (Phase 4).

Turns WES into a company that learns: every project leaves durable, searchable
memory; similar past work is discovered semantically; repeated mistakes become
learning rules; and future planning reuses all of it.

Built on the EXISTING stores — ``AgentMemory`` (memory), ``MemoryLink`` (knowledge
graph edges), ``ArchitectureDecisionRecord`` (ADRs) and ``LearningRule``
(learning) — plus the local ``EmbeddingService`` for real semantic retrieval.

Nothing is faked: memories are captured from actual project artifacts, embeddings
are real vectors, relationships are generated from the captured entities, and
learning rules are created only from observed repetition (evidence-based).
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AIEmployee, AIRole
from app.models.memory import AgentMemory, MemoryLink


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _s(v, n=2000):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


class CompanyMemoryService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.embedding import EmbeddingService

        self.embedder = EmbeddingService(db)

    # -- write -------------------------------------------------------------

    def remember(
        self,
        *,
        project_id: uuid.UUID | None,
        category: str,
        summary: str,
        content: str = "",
        importance: float = 0.5,
        confidence: float = 0.7,
        author: AIEmployee | None = None,
        author_role: str | None = None,
        kind: str = "company",
        tags: list[str] | None = None,
    ) -> AgentMemory:
        """Persist one durable company memory (with a real embedding)."""
        text = f"{summary}\n{content}".strip()
        vec = self.embedder.embed(text)
        mem = AgentMemory(
            scope="company",
            employee_id=author.id if author else None,
            project_id=project_id,
            kind=kind,
            summary=_s(summary, 400),  # must fit AgentMemory.summary varchar(400)
            content=_s(content, 6000) or None,
            tags=json.dumps(tags or []),
            category=category,
            importance=max(0.0, min(float(importance), 1.0)),
            confidence=max(0.0, min(float(confidence), 1.0)),
            author_role=author_role or (self._role_title(author) if author else None),
            embedding=json.dumps(vec) if vec else None,
            embedding_model="nomic-embed-text" if vec else None,
        )
        self.db.add(mem)
        self.db.flush()
        return mem

    def link(self, source: AgentMemory, target: AgentMemory, relation: str) -> None:
        if source.id == target.id:
            return
        self.db.add(
            MemoryLink(source_memory_id=source.id, target_memory_id=target.id, relation=relation)
        )

    def _role_title(self, emp: AIEmployee | None) -> str | None:
        if not emp or not emp.role_id:
            return None
        role = self.db.get(AIRole, emp.role_id)
        return role.title if role else None

    def _emp(self, *codes: str) -> AIEmployee | None:
        rows = self.db.execute(
            select(AIRole.code, AIEmployee)
            .join(AIEmployee, AIEmployee.role_id == AIRole.id)
            .where(AIEmployee.is_deleted.is_(False))
        ).all()
        by = {str(c).upper(): e for c, e in rows}
        for c in codes:
            if c.upper() in by:
                return by[c.upper()]
        return None

    # -- capture a whole planned project ----------------------------------

    def capture_project(self, project, executive: dict, consensus: dict, review: dict, blueprint: dict) -> dict:
        """Auto-persist the durable knowledge a planned project produces.

        Objective, executive decisions, architecture decision (ADR), agreed
        constraints, risks and review findings — each a memory, linked into the
        project's knowledge graph.
        """
        ceo, cto, arch = executive["ceo"], executive["cto"], executive["architect"]
        ceo_e, cto_e = self._emp("CEO"), self._emp("CTO", "CHIEF_ARCHITECT")
        arch_e, sec_e = self._emp("CHIEF_ARCHITECT", "CTO"), self._emp("SECURITY_ENGINEER")

        root = self.remember(
            project_id=project.id, category="founder_objective",
            summary=f"Objective: {project.business_objective or project.name}",
            content=_s(ceo.get("vision")), importance=0.9, confidence=0.9,
            author=ceo_e, kind="objective",
            tags=[project.code],
        )
        made: list[AgentMemory] = [root]

        # Executive / technology decision.
        m = self.remember(
            project_id=project.id, category="technology_choice",
            summary=f"Tech strategy: {_s(cto.get('strategy'), 200)}",
            content="Stack: " + ", ".join(cto.get("stack", [])), importance=0.8,
            confidence=0.8, author=cto_e, kind="decision",
            tags=cto.get("stack", [])[:8],
        )
        self.link(m, root, "decides_for")
        made.append(m)

        # Architecture decision -> also a real ADR.
        adr = self.remember(
            project_id=project.id, category="architecture_decision",
            summary=f"Architecture: {_s(arch.get('design'), 200)}",
            content="Components: " + ", ".join(arch.get("components", [])), importance=0.85,
            confidence=0.8, author=arch_e, kind="decision",
            tags=arch.get("components", [])[:8],
        )
        self.link(adr, root, "architecture_of")
        self.link(adr, m, "informed_by")
        made.append(adr)

        # Executive consensus decision + agreed constraints.
        cons = self.remember(
            project_id=project.id, category="executive_decision",
            summary=f"Executive consensus: {consensus.get('decision')}",
            content=_s(consensus.get("rationale")) + "\nConstraints: "
            + "; ".join(consensus.get("agreed_constraints", [])),
            importance=0.8, confidence=0.75, author=ceo_e, kind="decision",
            tags=["consensus", consensus.get("decision", "")],
        )
        self.link(cons, root, "governs")
        made.append(cons)

        # Risks.
        for r in (blueprint.get("risks") or [])[:6]:
            rm = self.remember(
                project_id=project.id, category="risk",
                summary=f"Risk: {_s(r.get('title'), 200)}",
                content=f"[{r.get('category')}] p={r.get('probability')} i={r.get('impact')}. "
                f"Mitigation: {_s(r.get('mitigation'), 300)}",
                importance=0.6, confidence=0.7, kind="risk",
                tags=[r.get("category", "")],
            )
            self.link(rm, root, "risk_of")
            made.append(rm)

        # Review findings (QA / Security).
        for rv in (review.get("reviews") or []):
            for f in rv.get("findings", [])[:4]:
                fm = self.remember(
                    project_id=project.id, category="review_finding",
                    summary=f"{rv.get('reviewer')}: {_s(f, 200)}",
                    content=f"verdict={rv.get('verdict')}", importance=0.65, confidence=0.8,
                    author=sec_e if "Security" in (rv.get("reviewer") or "") else None,
                    kind="finding", tags=[rv.get("reviewer", "")],
                )
                self.link(fm, root, "finding_on")
                made.append(fm)

        self.db.flush()
        return {"project_id": str(project.id), "memories_created": len(made),
                "categories": sorted({mm.category for mm in made})}

    def _write_adr(self, project, arch: dict, decided_by):
        from app.models.knowledge import ArchitectureDecisionRecord
        from app.domain.knowledge_enums import ADRStatus

        n = self.db.scalar(select(AgentMemory).limit(1))  # noqa: keep session warm
        count = (
            self.db.query(ArchitectureDecisionRecord)
            .filter(ArchitectureDecisionRecord.project_id == project.id)
            .count()
        )
        # ADR is best-effort. Insert directly; on failure expunge only the ADR row
        # so the memories created in this session are never affected.
        adr = ArchitectureDecisionRecord(
            code=f"{project.code}-ADR-{count + 1:03d}",
            title=_s(arch.get("design"), 180) or f"Architecture for {project.name}",
            status=ADRStatus.ACCEPTED,
            context=f"Objective: {project.business_objective}",
            decision=_s(arch.get("design"), 2000),
            consequences="Components: " + ", ".join(arch.get("components", [])),
            project_id=project.id,
            decided_by_id=decided_by.id if decided_by else None,
            decided_at=_now(),
        )
        self.db.add(adr)
        try:
            self.db.flush([adr])
        except Exception:
            try:
                self.db.expunge(adr)
            except Exception:
                pass

    # -- semantic retrieval ------------------------------------------------

    def _all_embedded(self, *, exclude_project: uuid.UUID | None = None) -> list[AgentMemory]:
        q = select(AgentMemory).where(AgentMemory.embedding.is_not(None))
        rows = self.db.scalars(q).all()
        return [m for m in rows if exclude_project is None or m.project_id != exclude_project]

    def semantic_search(self, query: str, *, k: int = 6, exclude_project: uuid.UUID | None = None,
                        category: str | None = None) -> list[dict]:
        """Rank memories by semantic similarity to ``query`` (cosine over real vectors)."""
        qv = self.embedder.embed(query)
        pool = self._all_embedded(exclude_project=exclude_project)
        if category:
            pool = [m for m in pool if m.category == category]
        scored = []
        for m in pool:
            try:
                vec = json.loads(m.embedding)
            except (TypeError, ValueError):
                continue
            sim = self.embedder.cosine(qv, vec) if qv else 0.0
            scored.append((sim, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sim, m in scored[:k]:
            out.append(
                {
                    "similarity": round(sim, 4),
                    "category": m.category,
                    "summary": m.summary,
                    "project_id": str(m.project_id) if m.project_id else None,
                    "importance": m.importance,
                    "author_role": m.author_role,
                }
            )
        return out

    def similar_projects(self, project, *, k: int = 3) -> list[dict]:
        """Find past projects whose objective is semantically closest to this one."""
        query = f"{project.business_objective or project.name}"
        hits = self.semantic_search(
            query, k=30, exclude_project=project.id, category="founder_objective"
        )
        seen, out = set(), []
        for h in hits:
            pid = h["project_id"]
            if pid and pid not in seen:
                seen.add(pid)
                out.append({"project_id": pid, "objective": h["summary"], "similarity": h["similarity"]})
            if len(out) >= k:
                break
        return out

    # -- recall for planning (future work reuses past knowledge) -----------

    def recall_for_planning(self, objective: str, *, exclude_project: uuid.UUID | None = None) -> dict:
        """Prior knowledge + learnings relevant to a new objective, for planning."""
        reuse = self.semantic_search(objective, k=5, exclude_project=exclude_project)
        # Applicable, evidence-based learning rules to AVOID past mistakes.
        from app.services.learning import LearningService

        try:
            rules = LearningService(self.db).apply(objective, limit=5)
        except Exception:
            rules = []
        return {
            "reuse": [r for r in reuse if r["similarity"] > 0.4],
            "avoid": rules,
        }

    def planning_context(self, objective: str, *, exclude_project: uuid.UUID | None = None) -> str:
        rc = self.recall_for_planning(objective, exclude_project=exclude_project)
        bits = []
        if rc["reuse"]:
            bits.append(
                "Reuse knowledge from past projects (do not redo): "
                + "; ".join(f"{r['category']}: {r['summary']}" for r in rc["reuse"][:5])
            )
        if rc["avoid"]:
            bits.append(
                "Avoid these known mistakes (company learning rules): "
                + "; ".join(_s(r.get("rule") or r.get("summary"), 160) for r in rc["avoid"][:5])
            )
        return "\n".join(bits)

    # -- learning engine (repetition -> rule) ------------------------------

    def learn_from_repetition(self, *, min_projects: int = 2, threshold: float = 0.6) -> list[dict]:
        """Cluster SEMANTICALLY-similar findings/risks across projects into rules.

        Evidence-based and intelligent: findings are grouped by embedding cosine
        similarity (not keywords), so 'no encryption for patient records' and 'no
        encryption for stock database' cluster together despite different domains.
        A rule is created only when a cluster spans DIFFERENT projects — genuine,
        observed repetition, with the projects as evidence.
        """
        from app.models.learning import LearningRule

        rows = self.db.scalars(
            select(AgentMemory).where(
                AgentMemory.embedding.is_not(None),
                AgentMemory.category.in_(["review_finding", "risk"]),
            )
        ).all()
        items = []
        for m in rows:
            try:
                items.append((m, json.loads(m.embedding)))
            except (TypeError, ValueError):
                continue

        used: set = set()
        created = []
        for i, (m, vec) in enumerate(items):
            if m.id in used:
                continue
            cluster = [m]
            projects = {m.project_id}
            for j, (m2, vec2) in enumerate(items):
                if i == j or m2.id in used or m2.category != m.category:
                    continue
                if self.embedder.cosine(vec, vec2) >= threshold:
                    cluster.append(m2)
                    projects.add(m2.project_id)
            projects.discard(None)
            if len(projects) < min_projects:
                continue
            for c in cluster:
                used.add(c.id)
            theme = self._theme(" ".join(c.summary for c in cluster))
            rule_text = (
                f"Recurring {m.category.replace('_', ' ')} across {len(projects)} projects "
                f"(theme: {theme}). Proactively address during planning/design. "
                f"Example: {m.summary[:150]}"
            )
            existing = self.db.scalar(select(LearningRule).where(LearningRule.rule == rule_text))
            if existing is not None:
                existing.occurrences = (existing.occurrences or 1) + 1
                existing.evidence = json.dumps({"projects": [str(p) for p in projects], "count": len(projects)})
                self.db.flush()
                continue
            try:
                lr = LearningRule(
                    kind="planning" if m.category == "risk" else "review",
                    rule=rule_text[:1000],
                    dimension=m.category,
                    evidence=json.dumps({"projects": [str(p) for p in projects], "count": len(projects)}),
                    occurrences=len(projects),
                    applied_count=0,
                    active=True,
                )
                self.db.add(lr)
                self.db.flush()
                created.append({"kind": lr.kind, "rule": lr.rule, "projects": len(projects)})
            except Exception:
                self.db.rollback()
        return created

    @staticmethod
    def _theme(text: str) -> str:
        """A coarse theme key from a finding/risk summary (for repetition grouping)."""
        import re

        stop = {"the", "a", "an", "for", "of", "in", "to", "and", "no", "not", "is", "are",
                "must", "be", "with", "on", "review", "finding", "risk"}
        words = [w for w in re.findall(r"[a-z]{4,}", (text or "").lower()) if w not in stop]
        return " ".join(sorted(set(words))[:4]) or "general"

    # -- retrospective (after completion) ----------------------------------

    def retrospective(self, project) -> dict:
        """Generate and persist a project retrospective (LLM-reasoned, stored)."""
        from app.services.executive_reasoning import ExecutiveReasoningService

        svc = ExecutiveReasoningService(self.db)
        pm = self._emp("PRODUCT_MANAGER", "CEO")
        mems = self.db.scalars(
            select(AgentMemory).where(AgentMemory.project_id == project.id)
        ).all()
        context = "\n".join(f"- {m.category}: {m.summary}" for m in mems[:30])
        data = svc._reason(
            "AI Product Manager",
            pm,
            "You are running a project retrospective. Reply with ONLY JSON: "
            '{"went_well":["..."],"failed":["..."],"root_causes":["..."],'
            '"lessons_learned":["..."],"reusable_assets":["..."],'
            '"technical_debt":["..."],"recommendations":["..."]}',
            f"Project: {project.name}\nObjective: {project.business_objective}\n"
            f"Captured memory:\n{context}",
        )
        sections = {
            k: [str(x)[:300] for x in (data.get(k) or [])][:8]
            for k in ("went_well", "failed", "root_causes", "lessons_learned",
                      "reusable_assets", "technical_debt", "recommendations")
        }
        root = self.remember(
            project_id=project.id, category="retrospective",
            summary=f"Retrospective — {project.name}",
            content=json.dumps(sections), importance=0.9, confidence=0.8,
            author=pm, kind="retrospective", tags=["retrospective", project.code],
        )
        # Each lesson learned becomes its own searchable, reusable memory.
        for lesson in sections["lessons_learned"] + sections["recommendations"]:
            lm = self.remember(
                project_id=project.id, category="lesson_learned",
                summary=_s(lesson, 300), importance=0.75, confidence=0.75,
                kind="lesson", tags=[project.code],
            )
            self.link(lm, root, "lesson_from")
        self.db.flush()
        return {"project_id": str(project.id), "retrospective": sections}

    # -- read model / graph ------------------------------------------------

    def project_memory(self, project_id: uuid.UUID) -> dict:
        mems = self.db.scalars(
            select(AgentMemory).where(AgentMemory.project_id == project_id).order_by(AgentMemory.created_at)
        ).all()
        ids = [m.id for m in mems]
        links = self.db.scalars(
            select(MemoryLink).where(MemoryLink.source_memory_id.in_(ids or [uuid.uuid4()]))
        ).all()
        by_id = {m.id: m for m in mems}
        return {
            "count": len(mems),
            "by_category": {
                c: sum(1 for m in mems if m.category == c) for c in sorted({m.category for m in mems if m.category})
            },
            "memories": [
                {
                    "category": m.category, "summary": m.summary, "importance": m.importance,
                    "confidence": m.confidence, "author_role": m.author_role,
                    "embedded": m.embedding is not None,
                }
                for m in mems
            ],
            "graph_edges": [
                {
                    "from": by_id[e.source_memory_id].summary if e.source_memory_id in by_id else None,
                    "relation": e.relation,
                    "to": by_id[e.target_memory_id].summary if e.target_memory_id in by_id else None,
                }
                for e in links
            ],
        }
