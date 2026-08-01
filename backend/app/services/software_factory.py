"""Delivery Intelligence & Software Factory (AURORA — Sprint 09).

Where the Founder watches products being built — not repositories, not code.
Composed entirely from signals that already exist; no new reasoning, no
duplicated logic:

* Project / FounderMissionControl — products, their business objective & stage
* DevelopmentSession / Job        — the live factory floor (who is doing what)
* QualityGateRun                  — the quality center
* ReleaseVersion / PipelineRun    — the release center
* KnowledgeNetwork / business_analysis — the dependency map & shared capabilities

Every value is business language. Commits, branches, PRs, CI logs, containers,
providers, prompts and tokens are never surfaced.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

# The nine business delivery stages the Founder sees (engineering never shown).
DELIVERY_STAGES = [
    "Business Analysis", "Architecture", "Implementation", "Quality Review",
    "Executive Review", "Founder Approval", "Release Preparation",
    "Customer Delivery", "Learning",
]
_STAGE_BLURB = {
    "Business Analysis": "Understanding the objective and shaping requirements.",
    "Architecture": "Designing the solution and reusing what the company already knows.",
    "Implementation": "Building the product.",
    "Quality Review": "Testing and reviewing the work against company standards.",
    "Executive Review": "The executive board evaluating the delivered work.",
    "Founder Approval": "Waiting for your authorisation to release.",
    "Release Preparation": "Preparing the release for delivery.",
    "Customer Delivery": "Delivering the product.",
    "Learning": "Capturing what was learned for the future.",
}
# Mission lifecycle stage -> business delivery stage.
_LIFECYCLE_TO_DELIVERY = {
    "Business Objective": "Business Analysis",
    "Business Understanding": "Business Analysis",
    "Executive Discussion": "Architecture",
    "Architecture": "Architecture",
    "Planning": "Implementation",
    "Engineering": "Implementation",
    "Testing": "Quality Review",
    "Review": "Executive Review",
    "Deployment": "Release Preparation",
    "Business Validation": "Customer Delivery",
    "Completed": "Learning",
}
# Live factory-floor role -> business persona + verb.
_FLOOR = {
    "planning": ("Business Analyst", "refining requirements"),
    "repo_analysis": ("Chief Architect", "reviewing existing company assets"),
    "knowledge": ("Chief Architect", "consulting company knowledge"),
    "intent": ("Business Analyst", "clarifying the work scope"),
    "implementation": ("Engineering", "implementing the product"),
    "git": ("Engineering", "securely saving the work"),
    "testing": ("Quality", "validating quality"),
    "self_debug": ("Engineering", "resolving issues automatically"),
    "review": ("Quality", "reviewing the work"),
    "board_review": ("Executive Board", "evaluating the delivery"),
    "quality_gate": ("Quality", "verifying quality standards"),
    "merge_readiness": ("DevOps", "confirming release readiness"),
    "documentation": ("Business Analyst", "documenting the product"),
    "pull_request": ("Engineering", "preparing work for your approval"),
    "security": ("Security", "reviewing for risk"),
    "merge": ("DevOps", "releasing approved work"),
}
_PORTFOLIO = {
    "active": "Active", "planning": "Planned", "on_hold": "Paused",
    "completed": "Completed", "archived": "Cancelled",
}


def _now():
    return datetime.now(timezone.utc)


def _loads(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


class SoftwareFactoryService:
    def __init__(self, db: Session):
        self.db = db
        from app.services.founder_mission_control import FounderMissionControlService

        self.mc = FounderMissionControlService(db)

    # ------------------------------------------------------------------ #
    #  Product pipeline                                                  #
    # ------------------------------------------------------------------ #

    def product_pipeline(self) -> dict:
        from app.models.work import Project

        projects = self.db.scalars(select(Project).order_by(Project.created_at.desc())).all()
        products = []
        for p in projects:
            if p.status in ("archived",):
                continue
            tasks = self.mc._mission_tasks(p.id)
            stage = self.mc._lifecycle_stage(p, tasks)
            delivery = _LIFECYCLE_TO_DELIVERY.get(stage, "Business Analysis")
            ba = _loads(p.business_analysis)
            domain = ba.get("domain_analysis") or {}
            analytics = self._analytics(p, tasks, stage)
            pending = self.mc._pending_decision(p, tasks)
            products.append({
                "product_id": str(p.id),
                "product": p.name,
                "business_objective": p.business_objective or (ba.get("vision")),
                "current_stage": delivery,
                "stage_blurb": _STAGE_BLURB.get(delivery, ""),
                "current_executive": self.mc._current_executive(stage),
                "delivery_confidence": analytics.get("confidence"),
                "expected_delivery": analytics.get("estimated_completion"),
                "business_value": domain.get("business_model") or ba.get("vision")
                or "Delivering on the founder's objective.",
                "current_risk": (self.mc._top_risks(ba, domain)[:1] or [None])[0],
                "dependencies": (domain.get("suggested_modules") or [])[:4],
                "founder_approval_status": "Awaiting your approval" if pending else (
                    "Released" if delivery in ("Customer Delivery", "Learning") else "Company-managed"),
                "progress": self.mc._progress_pct(stage),
                "priority": _v(p.priority),
            })
        active = [p for p in products if p["current_stage"] not in ("Learning",)]
        return {
            "products": products,
            "active": len(active),
            "awaiting_founder": len([p for p in products if p["founder_approval_status"] == "Awaiting your approval"]),
            "total": len(products),
        }

    # ------------------------------------------------------------------ #
    #  Delivery pipeline (the nine business stages)                      #
    # ------------------------------------------------------------------ #

    def delivery_pipeline(self) -> dict:
        pipeline = self.product_pipeline()["products"]
        counts = {s: 0 for s in DELIVERY_STAGES}
        for p in pipeline:
            counts[p["current_stage"]] = counts.get(p["current_stage"], 0) + 1
        stages = []
        for s in DELIVERY_STAGES:
            stages.append({
                "stage": s, "blurb": _STAGE_BLURB[s], "products": counts.get(s, 0),
                "product_names": [p["product"] for p in pipeline if p["current_stage"] == s][:5],
            })
        return {"stages": stages, "total_in_flight": len([p for p in pipeline if p["current_stage"] != "Learning"])}

    # ------------------------------------------------------------------ #
    #  Build intelligence (per product)                                  #
    # ------------------------------------------------------------------ #

    def build_intelligence(self, product_id) -> dict:
        import uuid as _uuid

        detail = self.mc.mission(_uuid.UUID(str(product_id)))
        stage = detail.get("current_stage")
        delivery = _LIFECYCLE_TO_DELIVERY.get(stage, "Business Analysis")
        return {
            "product": detail.get("mission_name"),
            "business_objective": detail.get("business_objective"),
            "current_progress": detail.get("overall_progress"),
            "current_stage": delivery,
            "what_is_happening": detail.get("current_activity") or _STAGE_BLURB.get(delivery),
            "why": self.mc._next_action(stage) if hasattr(self.mc, "_next_action") else _STAGE_BLURB.get(delivery),
            "who_is_responsible": detail.get("current_executive"),
            "confidence": detail.get("current_confidence"),
            "expected_outcome": detail.get("final_deliverables") or [],
            "business_impact": detail.get("business_impact") or detail.get("business_value"),
            "expected_delivery": detail.get("expected_completion"),
            "current_risk": detail.get("current_risk"),
            "timeline": detail.get("business_timeline"),
            "founder_decision": detail.get("pending_founder_decision"),
        }

    # ------------------------------------------------------------------ #
    #  Quality center                                                    #
    # ------------------------------------------------------------------ #

    def quality_center(self) -> dict:
        from app.models.quality import QualityGateRun

        rows = self.db.scalars(
            select(QualityGateRun).order_by(QualityGateRun.created_at.desc()).limit(200)).all()
        if not rows:
            return {
                "products_passing": 0, "products_requiring_attention": 0,
                "quality_trend": "steady", "review_quality": 0, "regression_confidence": 0,
                "release_confidence": 0, "average_score": 0,
                "note": "No products have reached quality review yet.",
            }
        passing = [r for r in rows if _v(r.status) in ("passed", "pass")]
        attention = [r for r in rows if _v(r.status) in ("failed",) or r.critical_count or r.high_count]
        avg = round(sum(r.overall_score for r in rows) / len(rows))
        # trend: recent third vs older third.
        recent = rows[: max(1, len(rows) // 3)]
        older = rows[-max(1, len(rows) // 3):]
        r_avg = sum(r.overall_score for r in recent) / len(recent)
        o_avg = sum(r.overall_score for r in older) / len(older)
        trend = "improving" if r_avg > o_avg + 2 else ("declining" if r_avg < o_avg - 2 else "steady")
        eligible = [r for r in rows if r.approval_eligible]
        tests = round(sum(r.tests_passed_pct for r in rows) / len(rows))
        return {
            "products_passing": len(passing),
            "products_requiring_attention": len(attention),
            "quality_trend": trend,
            "review_quality": avg,
            "regression_confidence": tests,
            "release_confidence": round(100 * len(eligible) / len(rows)),
            "average_score": avg,
            "reviews_performed": len(rows),
            "note": "Every product passes the review board and quality gate before release.",
        }

    # ------------------------------------------------------------------ #
    #  Release center                                                    #
    # ------------------------------------------------------------------ #

    def release_center(self) -> dict:
        from app.models.devops import PipelineRun, ReleaseVersion

        releases = self.db.scalars(
            select(ReleaseVersion).order_by(ReleaseVersion.created_at.desc()).limit(60)).all()
        pipelines = self.db.scalars(
            select(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(60)).all()

        def _rel(r):
            return {"release": r.version, "channel": r.channel, "status": _v(r.status)}

        completed = [_rel(r) for r in releases if _v(r.status) == "released"][:8]
        upcoming = [_rel(r) for r in releases if _v(r.status) in ("draft", "candidate")][:8]
        blocked = [{"release": p.code, "status": "blocked",
                    "note": "A step needs attention before release."}
                   for p in pipelines if _v(p.status) == "failed"][:6]
        delayed = [{"release": p.code, "status": "awaiting production approval"}
                   for p in pipelines if _v(p.status) == "awaiting_production"][:6]
        total_p = len(pipelines) or 1
        passed = len([p for p in pipelines if _v(p.status) == "passed"])
        return {
            "upcoming_releases": upcoming,
            "completed_releases": completed,
            "delayed_releases": delayed,
            "blocked_releases": blocked,
            "business_readiness": round(100 * len(completed) / max(1, len(releases))) if releases else 0,
            "deployment_readiness": round(100 * passed / total_p),
            "rollback_confidence": 95 if not blocked else 80,
            "note": "Releases pass staging validation; production delivery is Founder-authorised.",
        }

    # ------------------------------------------------------------------ #
    #  Dependency map                                                    #
    # ------------------------------------------------------------------ #

    def dependency_map(self) -> dict:
        from app.models.work import Project

        projects = self.db.scalars(select(Project).order_by(Project.created_at.desc()).limit(40)).all()
        products = []
        capability_owners: dict[str, dict] = {}
        for p in projects:
            if p.status == "archived":
                continue
            ba = _loads(p.business_analysis)
            domain = ba.get("domain_analysis") or {}
            modules = (domain.get("suggested_modules") or [])[:6]
            tasks = self.mc._mission_tasks(p.id)
            stage = self.mc._lifecycle_stage(p, tasks)
            products.append({
                "product": p.name,
                "executive_owner": self.mc._current_executive(stage),
                "shared_capabilities": modules,
                "risk": (self.mc._top_risks(ba, domain)[:1] or [None])[0],
            })
            for m in modules:
                capability_owners.setdefault(m, {"capability": m, "used_by": []})
                capability_owners[m]["used_by"].append(p.name)
        shared = [c for c in capability_owners.values() if len(c["used_by"]) > 1]
        reuse = {}
        try:
            reuse = self.mc.founder and {}  # placeholder to keep composition explicit
            from app.services.knowledge_network import KnowledgeNetworkService

            reuse = KnowledgeNetworkService(self.db).reuse_analysis()
        except Exception:
            reuse = {}
        return {
            "products": products,
            "shared_capabilities": sorted(shared, key=lambda c: -len(c["used_by"]))[:10],
            "knowledge_reuse": {
                "reuse_rate": reuse.get("reuse_rate") if isinstance(reuse, dict) else None,
                "assets_reused": reuse.get("total_reused") if isinstance(reuse, dict) else None,
                "note": "The company reuses proven work instead of rebuilding it.",
            },
            "risks": [{"product": p["product"], "risk": p["risk"]} for p in products if p["risk"]][:8],
        }

    # ------------------------------------------------------------------ #
    #  Software factory floor (live)                                     #
    # ------------------------------------------------------------------ #

    def factory_floor(self) -> dict:
        from app.models.development import DevelopmentSession
        from app.models.jobs import Job

        cutoff = _now() - timedelta(hours=12)
        sessions = self.db.scalars(
            select(DevelopmentSession)
            .where(DevelopmentSession.created_at >= cutoff)
            .order_by(DevelopmentSession.created_at.desc())
            .limit(60)
        ).all()
        stations = []
        seen = set()
        for s in sessions:
            persona, verb = _FLOOR.get(_v(s.stage), ("The company", "delivering work"))
            key = (persona, verb)
            if key in seen:
                continue
            seen.add(key)
            stations.append({
                "who": persona, "activity": verb,
                "state": "active" if _v(s.status) in ("running", "pending") else "recent",
            })
            if len(stations) >= 8:
                break
        running_jobs = self.db.scalar(
            select(func.count(Job.id)).where(Job.status.in_(("running", "queued", "pending")))) or 0
        if not stations:
            stations.append({"who": "The company", "activity": "monitoring for new work", "state": "idle"})
        return {
            "stations": stations,
            "live": any(st["state"] == "active" for st in stations) or running_jobs > 0,
            "active_operations": running_jobs,
            "note": "Your software company at work — expressed in business language.",
        }

    # ------------------------------------------------------------------ #
    #  Portfolio view                                                    #
    # ------------------------------------------------------------------ #

    def portfolio(self) -> dict:
        from app.models.work import Project

        projects = self.db.scalars(select(Project).order_by(Project.created_at.desc())).all()
        buckets: dict[str, list] = {v: [] for v in ("Active", "Completed", "Paused", "Planned", "Cancelled")}
        delivered = 0
        for p in projects:
            label = _PORTFOLIO.get(_v(p.status), "Active")
            ba = _loads(p.business_analysis)
            domain = ba.get("domain_analysis") or {}
            item = {
                "product": p.name,
                "business_objective": p.business_objective,
                "business_value": domain.get("business_model") or ba.get("vision")
                or "Delivering on the objective.",
                "priority": _v(p.priority),
            }
            buckets[label].append(item)
            if label == "Completed":
                delivered += 1
        total = len(projects) or 1
        aligned = len(buckets["Active"]) + len(buckets["Completed"])
        return {
            "active": buckets["Active"],
            "completed": buckets["Completed"],
            "paused": buckets["Paused"],
            "planned": buckets["Planned"],
            "cancelled": buckets["Cancelled"],
            "summary": {k: len(v) for k, v in buckets.items()},
            "business_value_delivered": delivered,
            "strategic_alignment": round(100 * aligned / total),
        }

    # ================================================================= #
    #  helpers                                                          #
    # ================================================================= #

    def _analytics(self, project, tasks, stage) -> dict:
        try:
            return self.mc.mission_analytics(project, tasks, stage)
        except Exception:
            return {"confidence": None, "estimated_completion": None}


def _v(x):
    return getattr(x, "value", x)
