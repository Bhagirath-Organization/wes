"""Project ATLAS — Repository Intelligence Engine (Sprint 01).

The execution-intelligence layer of WES: the company understands every connected
repository as a *business asset*, not just as source code.

This service COMPOSES the existing (Sprint 12) technical repository engine —
`RepositoryService`, `IndexerService`, and the `repo_analysis` analytics
(Architecture / Dependency / Documentation / Symbol) — and adds the business
layer on top: business understanding, codebase health, executive ownership,
Blueprint alignment, a structured repository graph, knowledge extraction into
the Company Brain, and a business-translated event store.

Guarantees:
* READ-ONLY with respect to repositories. It never modifies, pushes, branches,
  merges, tags or deletes. It only reads the index and writes WES's own
  intelligence / knowledge / memory tables.
* No engineering terminology is required for Founder understanding — every
  surfaced field is business language. Structured technical detail is stored in
  JSON for the company's own use, never surfaced verbatim to the Founder.
* No new reasoning is invented: business understanding is assembled
  deterministically from what the scanners already found (no LLM calls).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.repository import Repository, RepositoryMetrics, RepositorySymbol
from app.models.repository_intelligence import (
    RepositoryEvent,
    RepositoryGraphEdge,
    RepositoryGraphNode,
    RepositoryIntelligence,
)

# ---- Business translation: engineering event -> company (business) event ---- #
_EVENT_TRANSLATION = {
    "repository_created": ("The company connected a new software asset.", "asset"),
    "repository_analysed": ("The company analysed an existing software asset.", "analysis"),
    "branch_created": ("A new line of work began.", "delivery"),
    "pull_request": ("A business capability entered review.", "delivery"),
    "merge": ("Engineering completed a business capability.", "delivery"),
    "release": ("A new product version became available.", "release"),
    "tag": ("A product milestone was marked.", "release"),
    "issue": ("A potential improvement was logged.", "quality"),
    "discussion": ("A business discussion took place.", "collaboration"),
    "action": ("An automated company process ran.", "automation"),
}

# ---- Executive ownership model (fixed roster; responsibilities per role) ---- #
_OWNERSHIP = [
    ("Chief Executive", "Business value, priorities and strategic direction of this asset."),
    ("Chief Architect", "Architecture integrity, module boundaries and reuse."),
    ("Engineering Director", "Delivery, implementation quality and technical debt."),
    ("QA Director", "Quality, testing coverage and regression confidence."),
    ("Security Director", "Security posture, risk and compliance."),
    ("Business Analyst", "Business rules, requirements and domain knowledge."),
]

# Layers that indicate a shared / reusable capability seam.
_REUSE_HINTS = ("service", "utility", "shared", "lib", "common", "core", "component")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dump(v) -> str | None:
    try:
        return json.dumps(v)
    except Exception:
        return None


def _load(v, default=None):
    if not v:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


class RepositoryIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    # lazy sub-services (compose, never duplicate) ---------------------- #
    def _repos(self):
        from app.services.repository_service import IndexerService, RepositoryService

        return RepositoryService(self.db), IndexerService(self.db)

    def _analysis(self):
        from app.services.repo_analysis import (
            ArchitectureService,
            DependencyService,
            DocumentationService,
        )

        return (
            ArchitectureService(self.db),
            DependencyService(self.db),
            DocumentationService(self.db),
        )

    # ================================================================== #
    #  Repository Discovery                                              #
    # ================================================================== #

    def discover(self) -> dict:
        """Every connected repository, as a business asset."""
        repos, _ = self._repos()
        assets = []
        for r in repos.list_repositories():
            intel = self._intel_row(r.id)
            assets.append(self._asset_view(r, intel))
        understood = len([a for a in assets if a["business_status"] != "new"])
        return {
            "assets": assets,
            "total": len(assets),
            "understood": understood,
            "awaiting_understanding": len(assets) - understood,
            "note": "The company understands its repositories as business assets, not source code.",
        }

    def connected_repositories(self) -> dict:
        """Discover repositories the GitHub App can see (read-only), and mark
        which are already registered as WES business assets. Safe when the App
        is not configured (returns registered assets only)."""
        repos, _ = self._repos()
        registered = {r.slug: r for r in repos.list_repositories()}
        connected = []
        try:
            from app.services.github_service import GitHubService

            for gr in GitHubService().list_installation_repositories():
                slug = (gr.get("full_name") or gr.get("name") or "").lower()
                connected.append({
                    "name": gr.get("name"),
                    "full_name": gr.get("full_name"),
                    "purpose": gr.get("description") or "Not yet analysed.",
                    "language": gr.get("language"),
                    "default_branch": gr.get("default_branch"),
                    "visibility": "private" if gr.get("private") else "public",
                    "created": gr.get("created_at"),
                    "last_activity": gr.get("pushed_at"),
                    "registered": slug in registered,
                    "business_status": "understood" if slug in registered
                    and self._intel_row(registered[slug].id) else ("registered" if slug in registered else "discovered"),
                })
        except Exception:
            pass
        return {
            "connected": connected,
            "registered_count": len(registered),
            "discovered_count": len(connected),
            "github_configured": bool(connected),
            "note": "Connected software assets discovered via the company's GitHub App (read-only).",
        }

    def _asset_view(self, r: Repository, intel: RepositoryIntelligence | None) -> dict:
        frameworks = r.frameworks.split(",") if r.frameworks else []
        metrics = self.db.scalar(select(RepositoryMetrics).where(RepositoryMetrics.repository_id == r.id))
        return {
            "repository_id": str(r.id),
            "name": r.name,
            "purpose": (intel.business_objective if intel else None) or r.description or "Understanding in progress.",
            "business_capability": intel.business_capability if intel else None,
            "business_domain": intel.business_domain if intel else None,
            "project_ownership": str(r.project_id) if r.project_id else None,
            "executive_owner": intel.executive_owner if intel else None,
            "repository_health": round(intel.health_score) if intel else (round(metrics.health_score) if metrics else 0),
            "language": r.primary_language,
            "framework": frameworks[0] if frameworks else None,
            "technology_stack": frameworks,
            "created": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
            "last_activity": r.last_scanned_at.isoformat() if r.last_scanned_at else None,
            "visibility": "internal",
            "business_status": intel.business_status if intel else "new",
            "risk_level": intel.risk_level if intel else "unknown",
            "confidence": round(intel.confidence) if intel else 0,
        }

    # ================================================================== #
    #  Repository Understanding (the analysis pipeline)                  #
    # ================================================================== #

    def understand(self, repository_id: uuid.UUID, *, rescan: bool = False,
                   extract_knowledge: bool = True) -> dict:
        """Analyse a repository and capture business intelligence about it.

        Read-only w.r.t. the repository; idempotent. Ensures the technical index
        exists (reusing the Sprint-12 scanner), then derives and persists the
        business layer, the graph, Blueprint alignment, and knowledge.
        """
        repos, indexer = self._repos()
        r = repos.get(repository_id)  # raises NotFoundError if missing

        # 1) ensure the technical index exists (reuse existing scanner) ---- #
        if rescan or r.last_scanned_at is None:
            try:
                indexer.scan(r.id)
                self.db.refresh(r)
            except Exception:
                pass  # partial/empty repos still get a business view

        arch, dep, docs = self._analysis()
        metrics = self.db.scalar(select(RepositoryMetrics).where(RepositoryMetrics.repository_id == r.id))
        layers = arch.layers(r.id)
        modules = arch.modules(r.id)
        externals = dep.external_dependencies(r.id)
        module_graph = dep.module_graph(r.id)
        try:
            doc_links = docs.links(r.id)
        except Exception:
            doc_links = {}

        # 2) derive the business layer -------------------------------------- #
        business = self._derive_business(r)
        architecture_style = self._architecture_style(layers, modules)
        reusable = self._reusable_capabilities(layers, modules)
        health = self._compute_health(r, metrics, layers, modules, doc_links)
        risk_level, business_risk = self._risk(health, layers)
        maturity = self._maturity(metrics)
        confidence = self._confidence(metrics, layers, modules)
        owners = [{"executive": e, "responsibility": resp} for e, resp in _OWNERSHIP]
        executive_owner = self._primary_owner(architecture_style, risk_level)
        blueprint = self._blueprint_analysis(business, layers, reusable)

        structured = {
            "architecture": {
                "style": architecture_style,
                "layers": layers,
                "module_boundaries": [m["name"] for m in modules[:30]],
                "shared_libraries": reusable,
                "services": [l["name"] for l in layers if l["layer"] in ("service", "api", "backend")][:20],
                "api_relationships": module_graph.get("edges", [])[:100],
                "infrastructure": [l["name"] for l in layers if l["layer"] in ("configuration", "migration")][:20],
                "configuration": [l["name"] for l in layers if l["layer"] == "configuration"][:20],
            },
            "dependencies": {
                "internal": module_graph,
                "external_services": externals[:40],
                "reusable_modules": reusable,
            },
        }

        # 3) persist the intelligence row ----------------------------------- #
        intel = self._intel_row(r.id) or RepositoryIntelligence(repository_id=r.id)
        intel.business_domain = business["domain"]
        intel.business_objective = business["objective"]
        intel.business_capability = business["capability"]
        intel.business_value = business["value"]
        intel.business_status = business["status"]
        intel.architecture_style = architecture_style
        intel.maturity = maturity
        intel.risk_level = risk_level
        intel.business_risk = business_risk
        intel.documentation_quality = health["documentation_coverage"]
        intel.knowledge_coverage = health["knowledge_coverage"]
        intel.technical_debt = health["technical_debt"]
        intel.health_score = health["health_score"]
        intel.blueprint_coverage = blueprint["coverage"]
        intel.blueprint_alignment = blueprint["alignment"]
        intel.executive_owner = executive_owner
        intel.confidence = confidence
        intel.owners = _dump(owners)
        intel.modules = _dump([m["name"] for m in modules[:40]])
        intel.reusable_capabilities = _dump(reusable)
        intel.dependencies_summary = _dump({"external": externals[:20], "internal_edges": len(module_graph.get("edges", []))})
        intel.structured_intelligence = _dump(structured)
        intel.blueprint_analysis = _dump(blueprint)
        intel.analyzed_at = _now()
        if intel.id is None:
            self.db.add(intel)
        self.db.flush()

        # 4) knowledge extraction into the Company Brain -------------------- #
        knowledge = {"stored": 0}
        if extract_knowledge:
            knowledge = self._extract_knowledge(r, business, structured, reusable, blueprint)
            intel.knowledge_summary = _dump(knowledge)
            self.db.flush()

        # 5) rebuild the structured graph for this repository --------------- #
        self._rebuild_graph(r, business, modules, reusable, blueprint, executive_owner, externals)

        # 6) record the business-translated event --------------------------- #
        self.ingest_event(event_type="repository_analysed", repository_id=r.id,
                          detail=f"{r.name} understood as a business asset.", source="atlas")

        self.db.commit()
        return self.intelligence(r.id)

    # ---- business derivation (deterministic) -------------------------- #
    def _derive_business(self, r: Repository) -> dict:
        domain = None
        objective = r.description
        value = None
        status = "understood"
        # Prefer the linked Project's business framing when present.
        if r.project_id:
            try:
                from app.models.work import Project

                p = self.db.get(Project, r.project_id)
                if p is not None:
                    objective = p.business_objective or objective
                    ba = _load(p.business_analysis, {}) or {}
                    dom = (ba.get("domain_analysis") or {})
                    domain = dom.get("industry") or dom.get("domain")
                    value = dom.get("business_model") or ba.get("vision")
                    status = "active"
            except Exception:
                pass
        if not objective:
            objective = f"Software asset supporting {r.name}."
        capability = self._infer_capability(r, domain)
        if not value:
            value = "Supports the company's delivery of its objectives."
        return {"domain": domain or self._infer_domain(r), "objective": objective,
                "capability": capability, "value": value, "status": status}

    def _infer_domain(self, r: Repository) -> str:
        name = (r.name or "").lower() + " " + (r.description or "").lower()
        table = {
            "payment": "Payments", "expense": "Finance", "budget": "Finance", "invoice": "Finance",
            "health": "Healthcare", "hospital": "Healthcare", "patient": "Healthcare",
            "crm": "Customer Management", "customer": "Customer Management",
            "commerce": "E-commerce", "shop": "E-commerce", "cart": "E-commerce",
            "erp": "Operations", "inventory": "Operations", "logistics": "Operations",
            "url": "Web Services", "auth": "Identity & Access", "identity": "Identity & Access",
        }
        for k, v in table.items():
            if k in name:
                return v
        return "General Software"

    def _infer_capability(self, r: Repository, domain: str | None) -> str:
        fw = (r.frameworks or "").lower()
        lang = (r.primary_language or "").lower()
        if "react" in fw or "vue" in fw:
            return "Customer-facing web application"
        if "fastapi" in fw or "django" in fw or "flask" in fw or "express" in fw:
            return "Business service / API platform"
        if lang in ("python", "typescript", "javascript"):
            return "Business logic & automation"
        return "Software capability"

    # ---- architecture style --------------------------------------------- #
    def _architecture_style(self, layers: list[dict], modules: list[dict]) -> str:
        present = {l["layer"] for l in layers}
        if {"frontend", "backend"} <= present or {"frontend", "api"} <= present:
            return "Full-stack application"
        if {"api", "service", "model"} & present and "frontend" not in present:
            return "Layered backend service"
        if "frontend" in present and "backend" not in present:
            return "Web application"
        if "service" in present:
            return "Service-oriented"
        if len(modules) > 20:
            return "Modular monolith"
        return "Single-purpose module"

    def _reusable_capabilities(self, layers: list[dict], modules: list[dict]) -> list[str]:
        out = []
        for m in modules:
            path = (m.get("path") or m.get("name") or "").lower()
            if any(h in path for h in _REUSE_HINTS):
                out.append(m["name"])
        # layer-level services are reusable capability seams too
        for l in layers:
            if l["layer"] in ("service", "utility") and l["name"] not in out:
                out.append(l["name"])
        # de-dupe, keep order
        seen, uniq = set(), []
        for x in out:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return uniq[:15]

    # ---- codebase health ------------------------------------------------ #
    def _compute_health(self, r, metrics, layers, modules, doc_links) -> dict:
        # documentation: docstring coverage + markdown presence
        total_sym = self.db.scalar(
            select(func.count(RepositorySymbol.id)).where(RepositorySymbol.repository_id == r.id)) or 0
        documented = self.db.scalar(
            select(func.count(RepositorySymbol.id)).where(
                RepositorySymbol.repository_id == r.id, RepositorySymbol.docstring.isnot(None))) or 0
        doc_cov = round(100 * documented / total_sym) if total_sym else 0
        md = 0
        if isinstance(doc_links, dict):
            md = len(doc_links.get("documents", []) or doc_links.get("markdown", []) or [])
        if md:
            doc_cov = min(100, doc_cov + 10)
        health_score = round(metrics.health_score) if metrics and metrics.health_score else self._fallback_health(metrics, layers)
        tech_debt = round(metrics.technical_debt) if metrics and metrics.technical_debt is not None else 0
        # architecture consistency: layers well-formed vs sprawling modules
        consistency = 100 if layers else 60
        if len(modules) > 40 and len(layers) < 3:
            consistency = 65
        # knowledge coverage: extracted knowledge references for this repo
        from app.models.knowledge import KnowledgeReference

        kref = self.db.scalar(
            select(func.count(KnowledgeReference.id)).where(
                KnowledgeReference.entity_type == "repository",
                KnowledgeReference.entity_id == r.id)) or 0
        knowledge_cov = min(100, kref * 20)
        return {
            "documentation_coverage": doc_cov,
            "architecture_consistency": consistency,
            "configuration_quality": 90 if any(l["layer"] == "configuration" for l in layers) else 70,
            "technical_debt": tech_debt,
            "health_score": health_score,
            "knowledge_coverage": knowledge_cov,
        }

    def _fallback_health(self, metrics, layers) -> int:
        base = 60
        if layers:
            base += 15
        if metrics and metrics.test_file_count:
            base += 15
        return min(100, base)

    def _risk(self, health: dict, layers: list[dict]) -> tuple[str, str]:
        score = health["health_score"]
        debt = health["technical_debt"]
        if score >= 80 and debt < 20:
            return "low", "No material business risk detected."
        if score >= 65:
            return "moderate", "Some technical debt; manageable with normal maintenance."
        if score >= 50:
            return "elevated", "Rising technical debt could slow future delivery."
        return "high", "Significant debt or low health may threaten reliable delivery."

    def _maturity(self, metrics) -> str:
        if not metrics:
            return "emerging"
        files = metrics.file_count or 0
        if files > 400:
            return "mature"
        if files > 150:
            return "established"
        if files > 40:
            return "developing"
        return "emerging"

    def _confidence(self, metrics, layers, modules) -> int:
        c = 40
        if metrics and metrics.file_count:
            c += 25
        if layers:
            c += 20
        if modules:
            c += 15
        return min(100, c)

    def _primary_owner(self, style: str, risk: str) -> str:
        if risk in ("elevated", "high"):
            return "Engineering Director"
        if "Full-stack" in style or "Service" in style or "service" in style:
            return "Chief Architect"
        return "Chief Executive"

    # ---- Blueprint alignment engine ------------------------------------- #
    def _blueprint_analysis(self, business: dict, layers: list[dict], reusable: list[str]) -> dict:
        from app.services.company_brain import CompanyBrain

        index = CompanyBrain._blueprint_index()  # {volume_title: "topics..."}
        if not index:
            return {"coverage": 0, "alignment": 0, "missing_capabilities": [],
                    "architecture_alignment": "unknown", "business_alignment": "unknown",
                    "compliance": "unknown", "recommendations": [], "relevant_volumes": []}
        present_terms = " ".join(
            [l["layer"] for l in layers] + [l["name"] for l in layers] + reusable
            + [business.get("domain") or "", business.get("capability") or ""]).lower()
        expected = {
            "Security": "security" in present_terms or any(l["layer"] == "api" for l in layers),
            "Engineering System": bool(layers),
            "Technology Stack": True,
            "Quality": "test" in present_terms,
            "Knowledge Management": bool(reusable),
        }
        covered = sum(1 for v in expected.values() if v)
        coverage = round(100 * covered / len(expected))
        relevant = []
        for title in index:
            for area in expected:
                if area.lower() in title.lower():
                    relevant.append(title)
        missing = []
        recommendations = []
        if not expected["Quality"]:
            missing.append("Automated testing coverage")
            recommendations.append("Introduce automated tests to raise regression confidence.")
        if not expected["Security"]:
            missing.append("Explicit security boundary")
            recommendations.append("Add an authentication/authorisation layer per Security & Quality Blueprint.")
        if not expected["Knowledge Management"]:
            missing.append("Reusable capability documentation")
            recommendations.append("Capture reusable modules as company knowledge for future reuse.")
        alignment = round((coverage + (80 if layers else 40)) / 2)
        return {
            "coverage": coverage,
            "alignment": alignment,
            "architecture_alignment": "aligned" if layers else "partial",
            "business_alignment": "aligned" if business.get("objective") else "partial",
            "compliance": "compliant" if coverage >= 60 else "needs attention",
            "missing_capabilities": missing,
            "recommendations": recommendations,
            "relevant_volumes": sorted(set(relevant))[:5],
        }

    # ---- knowledge extraction into Company Brain ------------------------ #
    def _extract_knowledge(self, r, business, structured, reusable, blueprint) -> dict:
        """Store business concepts, capabilities and architecture decisions as
        company knowledge (documents linked to the repository) + one memory."""
        from app.domain.knowledge_enums import DocumentType, KnowledgeStatus
        from app.services.knowledge import KnowledgeService
        from app.services.knowledge_graph import ReferenceService

        stored = 0
        concepts = {
            "business_concepts": [business.get("domain"), business.get("capability")],
            "modules": structured["architecture"]["module_boundaries"][:20],
            "capabilities": reusable,
            "architecture_decisions": [structured["architecture"]["style"]],
        }
        try:
            ks = KnowledgeService(self.db, actor="ATLAS")
            refs = ReferenceService(self.db)
            title = f"Repository Intelligence — {r.name}"
            content = self._knowledge_markdown(r, business, structured, reusable, blueprint)
            # Idempotent: skip if a doc with this code already exists.
            code = f"REPO-{str(r.id)[:8].upper()}"
            existing = ks.get_by_code(code) if hasattr(ks, "get_by_code") else None
            if existing is None:
                doc = ks.create(
                    title=title, doc_type=DocumentType.ARCHITECTURE, content=content,
                    summary=f"How the company understands {r.name} as a business asset.",
                    keywords=",".join([c for c in concepts["capabilities"][:8] if c]),
                    code=code, status=KnowledgeStatus.APPROVED,
                )
                try:
                    refs.add(doc.id, "repository", entity_id=r.id, label=r.name)
                except Exception:
                    pass
                stored += 1
        except Exception:
            pass

        # one durable company memory (embedding is optional/offline-safe)
        try:
            from app.services.company_memory import CompanyMemoryService

            CompanyMemoryService(self.db).remember(
                project_id=r.project_id, category="repository_intelligence",
                summary=f"{r.name}: {business.get('capability')} in the {business.get('domain')} domain."[:400],
                content=f"Architecture: {structured['architecture']['style']}. "
                        f"Reusable: {', '.join(reusable[:6])}.",
                importance=0.6, confidence=0.7, kind="repository",
                tags=["repository", business.get("domain") or "software"],
            )
            stored += 1
        except Exception:
            pass

        return {"stored": stored, "concepts": concepts}

    def _knowledge_markdown(self, r, business, structured, reusable, blueprint) -> str:
        arch = structured["architecture"]
        lines = [
            f"# {r.name} — Business Asset Intelligence", "",
            f"**Business domain:** {business.get('domain')}",
            f"**Business capability:** {business.get('capability')}",
            f"**Objective:** {business.get('objective')}", "",
            f"## Architecture", f"Style: {arch['style']}",
            f"Modules: {', '.join(arch['module_boundaries'][:15])}",
            f"Reusable capabilities: {', '.join(reusable[:10]) or 'none identified'}", "",
            f"## Blueprint alignment",
            f"Coverage: {blueprint['coverage']}% · Compliance: {blueprint['compliance']}",
        ]
        if blueprint.get("recommendations"):
            lines += ["", "## Recommendations"] + [f"- {rec}" for rec in blueprint["recommendations"]]
        return "\n".join(lines)

    # ================================================================== #
    #  Structured views (read stored intelligence)                      #
    # ================================================================== #

    def intelligence(self, repository_id: uuid.UUID) -> dict:
        repos, _ = self._repos()
        r = repos.get(repository_id)
        intel = self._intel_row(r.id)
        if intel is None:
            return {"repository_id": str(r.id), "name": r.name, "understood": False,
                    "message": "This asset has not been understood yet."}
        owners = _load(intel.owners, [])
        return {
            "repository_id": str(r.id),
            "name": r.name,
            "understood": True,
            "business_domain": intel.business_domain,
            "business_objective": intel.business_objective,
            "business_capability": intel.business_capability,
            "business_value": intel.business_value,
            "business_status": intel.business_status,
            "architecture_style": intel.architecture_style,
            "maturity": intel.maturity,
            "risk_level": intel.risk_level,
            "business_risk": intel.business_risk,
            "documentation_quality": intel.documentation_quality,
            "knowledge_coverage": intel.knowledge_coverage,
            "health_score": intel.health_score,
            "blueprint_coverage": intel.blueprint_coverage,
            "blueprint_alignment": intel.blueprint_alignment,
            "executive_owner": intel.executive_owner,
            "confidence": intel.confidence,
            "reusable_capabilities": _load(intel.reusable_capabilities, []),
            "modules": _load(intel.modules, []),
            "owners": owners,
            "analyzed_at": intel.analyzed_at.isoformat() if intel.analyzed_at else None,
        }

    def architecture_intelligence(self, repository_id: uuid.UUID) -> dict:
        intel = self._intel_row(repository_id)
        s = _load(intel.structured_intelligence, {}) if intel else {}
        arch = (s or {}).get("architecture", {})
        return {
            "repository_id": str(repository_id),
            "architecture_style": (intel.architecture_style if intel else None),
            "application_architecture": arch.get("style"),
            "layer_structure": arch.get("layers", []),
            "module_boundaries": arch.get("module_boundaries", []),
            "shared_libraries": arch.get("shared_libraries", []),
            "services": arch.get("services", []),
            "api_relationships": len(arch.get("api_relationships", [])),
            "data_flow": self._data_flow(arch),
            "infrastructure": arch.get("infrastructure", []),
            "configuration": arch.get("configuration", []),
            "note": "Structured intelligence for the company's use; implementation detail is never shown to the Founder.",
        }

    def _data_flow(self, arch: dict) -> str:
        present = {l.get("layer") for l in arch.get("layers", [])}
        parts = [p for p in ("frontend", "api", "service", "model", "schema") if p in present]
        return " → ".join(p.title() for p in parts) if parts else "Single-tier"

    def dependency_intelligence(self, repository_id: uuid.UUID) -> dict:
        intel = self._intel_row(repository_id)
        s = _load(intel.structured_intelligence, {}) if intel else {}
        deps = (s or {}).get("dependencies", {})
        internal = deps.get("internal", {})
        externals = deps.get("external_services", [])
        return {
            "repository_id": str(repository_id),
            "internal_dependencies": len(internal.get("edges", [])),
            "shared_components": deps.get("reusable_modules", []),
            "shared_services": [e for e in deps.get("reusable_modules", []) if "service" in e.lower()],
            "reusable_modules": deps.get("reusable_modules", []),
            "external_services": externals,
            "infrastructure_dependencies": [e["package"] for e in externals if any(
                k in e["package"].lower() for k in ("docker", "postgres", "redis", "aws", "nginx"))],
            "business_impact": self._dependency_business_impact(externals, deps.get("reusable_modules", [])),
        }

    def _dependency_business_impact(self, externals, reusable) -> str:
        if len(reusable) >= 3:
            return "Strong internal reuse reduces cost and risk of future delivery."
        if len(externals) > 15:
            return "Relies on several external services; monitor for continuity risk."
        return "Dependencies are contained and pose limited business risk."

    def codebase_health(self, repository_id: uuid.UUID) -> dict:
        repos, _ = self._repos()
        r = repos.get(repository_id)
        intel = self._intel_row(r.id)
        if intel is None:
            return {"repository_id": str(r.id), "understood": False}
        return {
            "repository_id": str(r.id),
            "documentation_coverage": intel.documentation_quality,
            "architecture_consistency": _load(intel.blueprint_analysis, {}).get("alignment", intel.blueprint_alignment),
            "configuration_quality": 90 if intel.architecture_style else 70,
            "repository_maturity": intel.maturity,
            "reuse_opportunities": _load(intel.reusable_capabilities, []),
            "technical_debt_indicators": intel.technical_debt,
            "business_risk": intel.business_risk,
            "risk_level": intel.risk_level,
            "health_score": intel.health_score,
            "confidence": intel.confidence,
        }

    def blueprint_alignment(self, repository_id: uuid.UUID) -> dict:
        intel = self._intel_row(repository_id)
        if intel is None:
            return {"repository_id": str(repository_id), "understood": False}
        b = _load(intel.blueprint_analysis, {})
        return {
            "repository_id": str(repository_id),
            "coverage": b.get("coverage", intel.blueprint_coverage),
            "missing_capabilities": b.get("missing_capabilities", []),
            "architecture_alignment": b.get("architecture_alignment"),
            "business_alignment": b.get("business_alignment"),
            "compliance": b.get("compliance"),
            "recommendations": b.get("recommendations", []),
            "relevant_volumes": b.get("relevant_volumes", []),
        }

    def executive_ownership(self, repository_id: uuid.UUID) -> dict:
        intel = self._intel_row(repository_id)
        owners = _load(intel.owners, []) if intel else [
            {"executive": e, "responsibility": resp} for e, resp in _OWNERSHIP]
        return {
            "repository_id": str(repository_id),
            "primary_owner": intel.executive_owner if intel else "Chief Executive",
            "owners": owners,
        }

    def repository_memory(self, repository_id: uuid.UUID) -> dict:
        """What the company remembers about this repository."""
        from app.models.knowledge import ArchitectureDecisionRecord, KnowledgeReference
        from app.models.memory import AgentMemory
        from app.models.repository import RepositoryIssue

        repos, _ = self._repos()
        r = repos.get(repository_id)
        # memories tagged repository (best-effort)
        mems = self.db.scalars(
            select(AgentMemory).where(AgentMemory.category == "repository_intelligence")
            .order_by(AgentMemory.created_at.desc()).limit(20)).all()
        issues = self.db.scalars(
            select(RepositoryIssue).where(RepositoryIssue.repository_id == r.id)
            .order_by(RepositoryIssue.created_at.desc()).limit(20)).all()
        krefs = self.db.scalar(
            select(func.count(KnowledgeReference.id)).where(
                KnowledgeReference.entity_type == "repository",
                KnowledgeReference.entity_id == r.id)) or 0
        adrs = self.db.scalars(
            select(ArchitectureDecisionRecord).order_by(
                ArchitectureDecisionRecord.created_at.desc()).limit(10)).all()
        intel = self._intel_row(r.id)
        return {
            "repository_id": str(r.id),
            "architecture_decisions": [intel.architecture_style] if intel and intel.architecture_style else [],
            "reusable_modules": _load(intel.reusable_capabilities, []) if intel else [],
            "important_files": _load(intel.modules, [])[:10] if intel else [],
            "known_issues": [{"category": i.category, "message": i.message[:160]} for i in issues],
            "previous_reviews": krefs,
            "learning_history": [m.summary for m in mems][:10],
            "decision_records": [a.title for a in adrs][:10],
        }

    # ================================================================== #
    #  Repository graph                                                  #
    # ================================================================== #

    def _rebuild_graph(self, r, business, modules, reusable, blueprint, executive_owner, externals) -> None:
        from sqlalchemy import delete

        self.db.execute(delete(RepositoryGraphEdge).where(RepositoryGraphEdge.repository_id == r.id))
        self.db.execute(delete(RepositoryGraphNode).where(RepositoryGraphNode.repository_id == r.id))
        self.db.flush()

        repo_key = f"repo:{r.id}"
        nodes: list[tuple[str, str, str, dict]] = [(repo_key, "repository", r.name, {})]
        edges: list[tuple[str, str, str]] = []

        if r.project_id:
            pk = f"project:{r.project_id}"
            nodes.append((pk, "project", business.get("objective") or "Business project", {}))
            edges.append((repo_key, pk, "delivers"))
        # modules -> capabilities
        for m in modules[:20]:
            mk = f"module:{r.id}:{m['name']}"
            nodes.append((mk, "module", m["name"], {"path": m.get("path")}))
            edges.append((repo_key, mk, "contains"))
        for cap in reusable[:12]:
            ck = f"capability:{cap}"
            nodes.append((ck, "capability", cap, {}))
            edges.append((repo_key, ck, "provides"))
        # knowledge
        nodes.append((f"knowledge:{r.id}", "knowledge", f"{r.name} knowledge", {}))
        edges.append((repo_key, f"knowledge:{r.id}", "documents"))
        # blueprint volumes
        for vol in blueprint.get("relevant_volumes", [])[:5]:
            bk = f"blueprint:{vol}"
            nodes.append((bk, "blueprint", vol, {}))
            edges.append((repo_key, bk, "aligns_with"))
        # executive
        ek = f"executive:{executive_owner}"
        nodes.append((ek, "executive", executive_owner, {}))
        edges.append((repo_key, ek, "owned_by"))
        # dependencies
        for e in externals[:10]:
            dk = f"dependency:{e['package']}"
            nodes.append((dk, "dependency", e["package"], {"usages": e["usages"]}))
            edges.append((repo_key, dk, "depends_on"))

        for key, ntype, label, meta in nodes:
            self.db.add(RepositoryGraphNode(
                repository_id=r.id, node_key=key, node_type=ntype, label=label[:300], meta=_dump(meta)))
        for src, tgt, rel in edges:
            self.db.add(RepositoryGraphEdge(
                repository_id=r.id, source_key=src, target_key=tgt, relation=rel))
        self.db.flush()

    def graph(self, repository_id: uuid.UUID | None = None) -> dict:
        nq = select(RepositoryGraphNode)
        eq = select(RepositoryGraphEdge)
        if repository_id is not None:
            nq = nq.where(RepositoryGraphNode.repository_id == repository_id)
            eq = eq.where(RepositoryGraphEdge.repository_id == repository_id)
        nodes = self.db.scalars(nq.limit(2000)).all()
        edges = self.db.scalars(eq.limit(4000)).all()
        return {
            "nodes": [{"key": n.node_key, "type": n.node_type, "label": n.label,
                       "meta": _load(n.meta, {})} for n in nodes],
            "edges": [{"source": e.source_key, "target": e.target_key, "relation": e.relation} for e in edges],
            "levels": ["repository", "project", "module", "capability", "knowledge",
                       "blueprint", "executive", "dependency"],
        }

    # ================================================================== #
    #  Event ingestion + business translation + store                   #
    # ================================================================== #

    @staticmethod
    def translate_event(event_type: str, detail: str | None = None) -> tuple[str, str]:
        business, category = _EVENT_TRANSLATION.get(
            event_type, ("The company recorded an activity.", "activity"))
        return business, category

    def ingest_event(self, *, event_type: str, repository_id: uuid.UUID | None = None,
                     detail: str | None = None, source: str = "system",
                     external_ref: str | None = None,
                     occurred_at: datetime | None = None) -> RepositoryEvent:
        """Record an engineering event as a business-translated company event."""
        business, category = self.translate_event(event_type, detail)
        ev = RepositoryEvent(
            repository_id=repository_id, event_type=event_type, business_event=business,
            business_category=category, detail=detail, source=source,
            external_ref=external_ref, occurred_at=occurred_at or _now())
        self.db.add(ev)
        self.db.flush()
        return ev

    def events(self, repository_id: uuid.UUID | None = None, *, limit: int = 50) -> dict:
        q = select(RepositoryEvent).order_by(RepositoryEvent.created_at.desc())
        if repository_id is not None:
            q = q.where(RepositoryEvent.repository_id == repository_id)
        rows = self.db.scalars(q.limit(limit)).all()
        return {
            "events": [{
                "business_event": e.business_event,
                "category": e.business_category,
                "detail": e.detail,
                "when": (e.occurred_at or e.created_at).isoformat() if (e.occurred_at or e.created_at) else None,
            } for e in rows],
            "total": len(rows),
            "note": "Engineering activity, expressed as company events. No engineering terminology.",
        }

    # ================================================================== #
    #  helpers                                                           #
    # ================================================================== #

    def _intel_row(self, repository_id: uuid.UUID) -> RepositoryIntelligence | None:
        return self.db.scalar(
            select(RepositoryIntelligence).where(
                RepositoryIntelligence.repository_id == repository_id))
