"""Domain Intelligence — business understanding BEFORE engineering (Phase B).

This is a permanent Company-Brain capability, not a new reasoning stack. It reuses
``CompanyBrain`` (which already fuses company memory, learning rules, repository
intelligence and the Blueprint) and the executive provider plumbing to turn a bare
business objective into a structured **Business Understanding Report** — the
mandatory first activity of every project. Planning/architecture/engineering may
only begin after this report exists.

The six engines named in the mission are realised as capabilities of this one
service (no duplicated LLM plumbing):

* Industry Knowledge Engine        -> industry, best practices, existing solutions
* Business Understanding Engine     -> business model, users, pain points, KPIs
* Operational Intelligence Engine   -> daily operations, constraints, dependencies
* Business Process Discovery Engine -> departments, roles, approvals, events, docs
* Business Modelling Engine         -> capability/process maps, entities, matrices
* Domain Intelligence Engine        -> the orchestration + confidence + memory

No hardcoded industries: the model generalises to any domain. Grounded, not
templated — every field is produced by live reasoning over real company context.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session


def _s(v, n=800):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v).strip()[:n]


def _slist(v, n=12, cap=300):
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    out = []
    for x in v:
        if isinstance(x, dict):
            x = x.get("name") or x.get("title") or x.get("value") or "; ".join(
                f"{k}: {vv}" for k, vv in x.items())
        s = str(x).strip()[:cap]
        if s:
            out.append(s)
    return out[:n]


class DomainIntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.company_brain import CompanyBrain

        self.brain = CompanyBrain(db)          # reuse Phase A — never duplicate
        self._exec = self.brain._exec          # reuse provider + JSON plumbing

    # ------------------------------------------------------------------ #
    #  The Business Understanding Report (mandatory pre-planning output)  #
    # ------------------------------------------------------------------ #

    def understand(self, objective: str, *, project_id: uuid.UUID | None = None,
                   context: str = "") -> dict:
        """Produce the full Business Understanding Report for a business objective.

        Two focused reasoning passes (understanding + business model), each grounded
        in Company-Brain intelligence (similar past industries, learning rules,
        Blueprint). Returns a business-language report plus a confidence score.
        """
        intel = self.brain.intelligence(objective, project_id=project_id)
        intel_text = self.brain.intel_text(intel)
        emp = self._exec._employee_for_role("PRODUCT_MANAGER", "CEO")

        understanding = self._understanding_pass(objective, context, intel_text, emp)
        model = self._business_model_pass(objective, understanding, intel_text, emp)

        report = {**understanding, **model}
        report["industry_best_practices_applied"] = intel.get("blueprint", [])
        report["reused_industry_knowledge"] = intel.get("similar_projects", [])
        report["business_confidence"] = self._confidence(report)
        report["analyst"] = emp.name if emp else "AI Product Manager"
        return report

    # -- pass 1: industry + operations + users + compliance + KPIs --------

    def _understanding_pass(self, objective, context, intel_text, emp) -> dict:
        instruction = (
            "You are the AI Business Analyst of a software company. Before any "
            "engineering, deeply UNDERSTAND the business. Identify the real industry, "
            "how the business operates day to day, who is involved, what hurts today, "
            "what rules and regulations apply, and what success looks like. Generalise "
            "to ANY industry from first principles — do not invent facts. Use the "
            "company intelligence provided. Reply with ONLY this JSON object:\n"
            '{"industry":"...","business_model":"...","daily_operations":["..."],'
            '"stakeholders":["..."],"user_types":["..."],'
            '"operational_constraints":["..."],"compliance":["..."],'
            '"business_risks":["..."],"kpis":["..."],'
            '"pain_points":["..."],"industry_best_practices":["..."],'
            '"existing_solutions":["..."],"future_scalability":["..."],'
            '"understanding_confidence":0.0}'
        )
        prompt = (
            f"Business objective: {objective}\n{context}\n\n"
            f"COMPANY INTELLIGENCE:\n{intel_text}"
        )
        data = self._exec._reason("AI Business Analyst", emp, instruction, prompt)
        return {
            "industry": _s(data.get("industry"), 200),
            "business_model": _s(data.get("business_model"), 600),
            "daily_operations": _slist(data.get("daily_operations")),
            "stakeholders": _slist(data.get("stakeholders")),
            "user_types": _slist(data.get("user_types")),
            "operational_constraints": _slist(data.get("operational_constraints")),
            "compliance": _slist(data.get("compliance")),
            "business_risks": _slist(data.get("business_risks")),
            "kpis": _slist(data.get("kpis")),
            "pain_points": _slist(data.get("pain_points")),
            "industry_best_practices": _slist(data.get("industry_best_practices")),
            "existing_solutions": _slist(data.get("existing_solutions")),
            "future_scalability": _slist(data.get("future_scalability")),
            "_understanding_confidence": _conf(data.get("understanding_confidence")),
        }

    # -- pass 2: departments/processes/approvals + suggested assets -------

    def _business_model_pass(self, objective, understanding, intel_text, emp) -> dict:
        instruction = (
            "You are the AI Business Architect. Given the business understanding, model "
            "HOW this business runs and what software it needs. Discover the real "
            "departments, roles, approval flows, business events, master data, "
            "transactions, documents, and the modules/dashboards/reports/KPIs the "
            "software should provide. Recommend what to automate and a growth roadmap. "
            "Base everything on the specific business, not a generic template. Reply "
            "with ONLY this JSON object:\n"
            '{"departments":["..."],"roles":["..."],"approval_flows":["..."],'
            '"business_events":["..."],"master_data":["..."],"transactions":["..."],'
            '"business_documents":["..."],"automation_opportunities":["..."],'
            '"suggested_modules":["..."],"suggested_dashboards":["..."],'
            '"suggested_reports":["..."],"suggested_kpis":["..."],'
            '"roadmap":["..."],"modelling_confidence":0.0}'
        )
        prompt = (
            f"Business objective: {objective}\n"
            f"Industry: {understanding.get('industry')}\n"
            f"Business model: {understanding.get('business_model')}\n"
            f"Pain points: {', '.join(understanding.get('pain_points', [])[:5])}\n\n"
            f"COMPANY INTELLIGENCE:\n{intel_text}"
        )
        data = self._exec._reason("AI Business Architect", emp, instruction, prompt)
        return {
            "departments": _slist(data.get("departments")),
            "roles": _slist(data.get("roles")),
            "approval_flows": _slist(data.get("approval_flows")),
            "business_events": _slist(data.get("business_events")),
            "master_data": _slist(data.get("master_data")),
            "transactions": _slist(data.get("transactions")),
            "business_documents": _slist(data.get("business_documents")),
            "automation_opportunities": _slist(data.get("automation_opportunities")),
            "suggested_modules": _slist(data.get("suggested_modules")),
            "suggested_dashboards": _slist(data.get("suggested_dashboards")),
            "suggested_reports": _slist(data.get("suggested_reports")),
            "suggested_kpis": _slist(data.get("suggested_kpis")),
            "roadmap": _slist(data.get("roadmap")),
            "_modelling_confidence": _conf(data.get("modelling_confidence")),
        }

    # -- confidence: model self-report tempered by real coverage ----------

    @staticmethod
    def _confidence(report: dict) -> float:
        model_conf = (report.get("_understanding_confidence", 0.0)
                      + report.get("_modelling_confidence", 0.0)) / 2 or 0.5
        # Coverage: how many of the key sections were actually populated.
        key_sections = [
            "industry", "business_model", "daily_operations", "stakeholders",
            "user_types", "compliance", "business_risks", "kpis", "pain_points",
            "departments", "roles", "approval_flows", "suggested_modules",
            "suggested_reports", "suggested_kpis",
        ]
        filled = sum(1 for k in key_sections if report.get(k))
        coverage = filled / len(key_sections)
        return round(min(1.0, 0.5 * model_conf + 0.5 * coverage), 2)

    # -- compact business summary the executives/founder consume ----------

    @staticmethod
    def summary_text(report: dict) -> str:
        """Business-language digest for injection into executive reasoning."""
        bits = [
            f"Industry: {report.get('industry')}",
            f"Business model: {report.get('business_model')}",
        ]
        for label, key in (
            ("Stakeholders", "stakeholders"), ("Users", "user_types"),
            ("Pain points", "pain_points"), ("Compliance", "compliance"),
            ("KPIs", "kpis"), ("Departments", "departments"),
            ("Approvals", "approval_flows"),
            ("Suggested modules", "suggested_modules"),
            ("Suggested reports", "suggested_reports"),
        ):
            vals = report.get(key) or []
            if vals:
                bits.append(f"{label}: {', '.join(map(str, vals[:6]))}")
        return "\n".join(bits)

    # ------------------------------------------------------------------ #
    #  Domain memory — every project improves company knowledge          #
    # ------------------------------------------------------------------ #

    def remember_domain(self, project, report: dict) -> None:
        """Persist reusable domain knowledge so future projects recall it."""
        try:
            from app.services.company_memory import CompanyMemoryService

            mem = CompanyMemoryService(self.db)
            industry = report.get("industry") or "general"
            for category, value in (
                ("industry_knowledge", f"{industry}: {report.get('business_model')}"),
                ("operational_workflow", "; ".join(report.get("daily_operations", [])[:6])),
                ("business_rules", "; ".join(report.get("approval_flows", [])[:6])),
                ("kpis", "; ".join(report.get("kpis", [])[:6])),
                ("compliance_knowledge", "; ".join(report.get("compliance", [])[:6])),
                ("automation_patterns", "; ".join(report.get("automation_opportunities", [])[:6])),
            ):
                if _s(value):
                    mem.remember(
                        project_id=getattr(project, "id", None),
                        category=category,
                        summary=f"[{industry}] {category}: {_s(value, 300)}",
                        content=_s(value, 1500),
                        kind="domain",
                        author_role="AI Business Analyst",
                        importance=0.7,
                    )
        except Exception:
            # Memory capture is best-effort; never fail the analysis on it.
            pass


def _conf(v) -> float:
    try:
        c = float(v)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(c, 1.0))
