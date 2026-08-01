"""Founder Operating System endpoints (Phase 6 — final).

The single executive interface over the completed AI company. The Founder
supplies a business objective and sees business information; everything
technical is performed autonomously by Phases 1–5.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission
from app.services.founder_os import FounderOSService

router = APIRouter(prefix="/founder", tags=["founder"])
_read = Depends(require_permission(Permission.DASHBOARD_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


class ObjectiveRequest(BaseModel):
    """The ONLY input the Founder must provide."""

    objective: str = Field(min_length=3, max_length=4000)
    constraints: list[str] | None = None
    priority: str | None = None
    deadline: str | None = None
    budget: str | None = None
    success_criteria: str | None = None
    code: str | None = None
    name: str | None = None
    auto_plan: bool = True


@router.post("/objectives", dependencies=[_write], status_code=201)
def submit_objective(payload: ObjectiveRequest, db: Session = Depends(get_db)) -> dict:
    """Submit a business objective; the AI company does everything else."""
    return {"data": FounderOSService(db).submit_objective(**payload.model_dump())}


@router.get("/dashboard", dependencies=[_read])
def dashboard(db: Session = Depends(get_db)) -> dict:
    """Executive workspace — business information only."""
    return {"data": FounderOSService(db).executive_dashboard()}


@router.get("/decisions", dependencies=[_read])
def decisions(db: Session = Depends(get_db)) -> dict:
    """Only the decisions that genuinely require Founder authority."""
    return {"data": FounderOSService(db).decisions()}


@router.get("/governance", dependencies=[_read])
def governance(db: Session = Depends(get_db)) -> dict:
    """Company self-monitoring across the eight quality dimensions."""
    return {"data": FounderOSService(db).governance()}


@router.get("/continuity", dependencies=[_read])
def continuity(db: Session = Depends(get_db)) -> dict:
    """Business-continuity posture: what is durably stored."""
    return {"data": FounderOSService(db).continuity()}


@router.get("/report/{project_id}", dependencies=[_read])
def executive_report(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Automatic executive report for a project."""
    return {"data": FounderOSService(db).executive_report(project_id)}


# -- Founder Mission Control (Phase D) — business-language company view --------


@router.get("/missions", dependencies=[_read])
def missions(db: Session = Depends(get_db)) -> dict:
    """All business missions with their current lifecycle stage and progress."""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).missions()}


@router.get("/missions/{project_id}", dependencies=[_read])
def mission(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Full Mission Dashboard for one mission — entirely in business language."""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).mission(project_id)}


@router.get("/missions/{project_id}/timeline", dependencies=[_read])
def mission_timeline(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Executive timeline — every internal activity translated to business language."""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).executive_timeline(project_id)}


@router.get("/company-health", dependencies=[_read])
def company_health(db: Session = Depends(get_db)) -> dict:
    """Real-time company health across executive, quality, deployment, knowledge…"""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).company_health()}


@router.get("/risks", dependencies=[_read])
def risk_center(db: Session = Depends(get_db)) -> dict:
    """Risk Center — meaningful business/engineering risks, escalated only."""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).risk_center()}


@router.get("/inbox", dependencies=[_read])
def founder_inbox(db: Session = Depends(get_db)) -> dict:
    """Founder Inbox — approvals, decisions, critical risks, completed missions."""
    from app.services.founder_mission_control import FounderMissionControlService

    return {"data": FounderMissionControlService(db).inbox()}


@router.get("/evolution", dependencies=[_read])
def company_evolution(db: Session = Depends(get_db)) -> dict:
    """Company self-improvement — executive recommendations only (Phase E)."""
    from app.services.company_evolution import CompanyEvolutionService

    return {"data": CompanyEvolutionService(db).founder_view()}


# -- Executive Office (AURORA Sprint 02) — the Founder's conversation ----------


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    speaker: str | None = "CEO"


class InviteRequest(BaseModel):
    executive: str = Field(min_length=1, max_length=60)


class MeetingRequest(BaseModel):
    topic: str | None = None


def _office(db: Session):
    from app.services.executive_office import ExecutiveOfficeService

    return ExecutiveOfficeService(db)


@router.get("/executive/brief")
def executive_brief(
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.DASHBOARD_READ)),
) -> dict:
    """The CEO's opening brief when the Founder enters the Executive Office."""
    name = getattr(user, "full_name", None) or "Founder"
    return {"data": _office(db).brief(founder_name=name)}


@router.post("/executive/ask", dependencies=[_read])
def executive_ask(payload: AskRequest, db: Session = Depends(get_db)) -> dict:
    """Ask the executive team anything; answered from live company state."""
    return {"data": _office(db).ask(payload.question, speaker=payload.speaker or "CEO")}


@router.post("/executive/invite", dependencies=[_read])
def executive_invite(payload: InviteRequest, db: Session = Depends(get_db)) -> dict:
    """Invite an executive (CTO / Architect / QA / Security / …) into the room."""
    return {"data": _office(db).invite(payload.executive)}


@router.post("/executive/meeting", dependencies=[_read])
def executive_meeting(payload: MeetingRequest, db: Session = Depends(get_db)) -> dict:
    """Convene an executive meeting; minutes are captured to company knowledge."""
    return {"data": _office(db).meeting(payload.topic)}


@router.get("/executive/status", dependencies=[_read])
def executive_status(db: Session = Depends(get_db)) -> dict:
    """Live status rail for the Executive Office."""
    return {"data": _office(db).status()}


# -- Mission Center + Living Company (AURORA Sprint 03) ------------------------


def _center(db: Session):
    from app.services.mission_center import MissionCenterService

    return MissionCenterService(db)


@router.get("/live", dependencies=[_read])
def live_company(db: Session = Depends(get_db)) -> dict:
    """Living Company — every executive's live status, thinking and objective."""
    return {"data": _center(db).live_company()}


@router.get("/missions/{project_id}/detail", dependencies=[_read])
def mission_detail(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Full Mission Intelligence: stages, map, discussions, brain, risks, decisions."""
    return {"data": _center(db).mission_detail(project_id)}


@router.get("/mission-analytics", dependencies=[_read])
def mission_analytics(db: Session = Depends(get_db)) -> dict:
    """Mission analytics — throughput, confidence, workload, bottlenecks."""
    return {"data": _center(db).analytics()}


# -- Company Brain (AURORA Sprint 04) — the live intelligence center -----------


def _brain(db: Session):
    from app.services.company_brain_view import CompanyBrainViewService

    return CompanyBrainViewService(db)


@router.get("/brain/home", dependencies=[_read])
def brain_home(db: Session = Depends(get_db)) -> dict:
    """What is the company thinking about right now — topics, references, stream."""
    return {"data": _brain(db).home()}


@router.get("/brain/mission/{project_id}", dependencies=[_read])
def brain_mission(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Reasoning Explorer + blueprint + domain + memory + repository + graph."""
    return {"data": _brain(db).mission(project_id)}


@router.get("/brain/memory", dependencies=[_read])
def brain_memory(db: Session = Depends(get_db)) -> dict:
    """Memory Center — what the company remembered and the mistakes it avoids."""
    return {"data": _brain(db).memory()}


@router.get("/brain/learning", dependencies=[_read])
def brain_learning(db: Session = Depends(get_db)) -> dict:
    """Learning Center — new knowledge, patterns, opportunities, learning score."""
    return {"data": _brain(db).learning()}


@router.get("/brain/repository", dependencies=[_read])
def brain_repository(db: Session = Depends(get_db)) -> dict:
    """Repository Intelligence — reusable capabilities in business language."""
    return {"data": _brain(db).repository()}


@router.get("/brain/search", dependencies=[_read])
def brain_search(q: str = "", db: Session = Depends(get_db)) -> dict:
    """Universal semantic search across the company's intelligence."""
    return {"data": _brain(db).search(q)}


# -- AI Workforce (AURORA Sprint 05) -----------------------------------------


def _workforce(db: Session):
    from app.services.workforce import WorkforceService

    return WorkforceService(db)


@router.get("/workforce/home", dependencies=[_read])
def workforce_home(db: Session = Depends(get_db)) -> dict:
    """The AI organisation: teams, live members, who's engaged vs available."""
    return {"data": _workforce(db).home()}


@router.get("/workforce/employee/{employee_id}", dependencies=[_read])
def workforce_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """One AI employee's full profile — role, work, performance, collaboration."""
    return {"data": _workforce(db).employee(employee_id)}


@router.get("/workforce/org-chart", dependencies=[_read])
def workforce_org_chart(db: Session = Depends(get_db)) -> dict:
    """Founder → CEO → departments → employees."""
    return {"data": _workforce(db).org_chart()}


@router.get("/workforce/collaboration", dependencies=[_read])
def workforce_collaboration(db: Session = Depends(get_db)) -> dict:
    """The collaboration network, derived from real handoffs."""
    return {"data": _workforce(db).collaboration()}


@router.get("/workforce/hiring", dependencies=[_read])
def workforce_hiring(db: Session = Depends(get_db)) -> dict:
    """Future-workforce pipeline (planning only)."""
    return {"data": _workforce(db).hiring_pipeline()}


@router.get("/workforce/search", dependencies=[_read])
def workforce_search(q: str = "", db: Session = Depends(get_db)) -> dict:
    """Universal workforce search."""
    return {"data": _workforce(db).search(q)}


# -- Knowledge Network (AURORA Sprint 06) ------------------------------------


def _knet(db: Session):
    from app.services.knowledge_network import KnowledgeNetworkService

    return KnowledgeNetworkService(db)


@router.get("/knowledge-network/home", dependencies=[_read])
def knet_home(db: Session = Depends(get_db)) -> dict:
    """Knowledge health, growth, coverage, reuse, freshness + recent learnings."""
    return {"data": _knet(db).home()}


@router.get("/knowledge-network/graph", dependencies=[_read])
def knet_graph(db: Session = Depends(get_db)) -> dict:
    """The knowledge graph across missions, departments, executives, blueprint."""
    return {"data": _knet(db).graph()}


@router.get("/knowledge-network/timeline", dependencies=[_read])
def knet_timeline(db: Session = Depends(get_db)) -> dict:
    """Business-language timeline of what the company has learned."""
    return {"data": _knet(db).timeline()}


@router.get("/knowledge-network/memory", dependencies=[_read])
def knet_memory(db: Session = Depends(get_db)) -> dict:
    """Organisational memory — lessons, mistakes avoided, patterns, ageing."""
    return {"data": _knet(db).organisational_memory()}


@router.get("/knowledge-network/reuse", dependencies=[_read])
def knet_reuse(db: Session = Depends(get_db)) -> dict:
    """Reuse analysis — frequently/never reused, consolidation, opportunities."""
    return {"data": _knet(db).reuse_analysis()}


@router.get("/knowledge-network/blueprint", dependencies=[_read])
def knet_blueprint(db: Session = Depends(get_db)) -> dict:
    """Blueprint intelligence — adoption, compliance, coverage, gaps."""
    return {"data": _knet(db).blueprint()}


@router.get("/knowledge-network/insights", dependencies=[_read])
def knet_insights(db: Session = Depends(get_db)) -> dict:
    """Knowledge insights — most valuable, fastest growing, at risk."""
    return {"data": _knet(db).insights()}


@router.get("/knowledge-network/collaboration", dependencies=[_read])
def knet_collaboration(db: Session = Depends(get_db)) -> dict:
    """Which departments create knowledge together."""
    return {"data": _knet(db).collaboration()}


@router.get("/knowledge-network/search", dependencies=[_read])
def knet_search(q: str = "", db: Session = Depends(get_db)) -> dict:
    """Universal semantic search across the company's knowledge."""
    return {"data": _knet(db).search(q)}


# -- Founder Command Center (AURORA Sprint 07) -------------------------------


def _cmd(db: Session):
    from app.services.command_center import CommandCenterService

    return CommandCenterService(db)


@router.get("/command/overview", dependencies=[_read])
def command_overview(db: Session = Depends(get_db)) -> dict:
    """Executive overview — headline KPIs + what needs attention."""
    return {"data": _cmd(db).overview()}


@router.get("/command/brief")
def command_brief(
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.DASHBOARD_READ)),
) -> dict:
    """Today's Executive Brief."""
    name = getattr(user, "full_name", None) or "Founder"
    return {"data": _cmd(db).daily_brief(name)}


@router.get("/command/scoreboard", dependencies=[_read])
def command_scoreboard(db: Session = Depends(get_db)) -> dict:
    """Executive scoreboard — responsibility, workload, confidence, ownership."""
    return {"data": _cmd(db).scoreboard()}


@router.get("/command/mission-performance", dependencies=[_read])
def command_mission_performance(db: Session = Depends(get_db)) -> dict:
    """Mission performance — velocity, bottlenecks, forecast."""
    return {"data": _cmd(db).mission_performance()}


@router.get("/command/decisions", dependencies=[_read])
def command_decisions(db: Session = Depends(get_db)) -> dict:
    """Unified decision command queue."""
    return {"data": _cmd(db).decision_command()}


@router.get("/command/predictions", dependencies=[_read])
def command_predictions(db: Session = Depends(get_db)) -> dict:
    """Predictive insights composed from real signals (with confidence)."""
    return {"data": _cmd(db).predictions()}


@router.get("/command/health", dependencies=[_read])
def command_health(db: Session = Depends(get_db)) -> dict:
    """Company health across ten areas."""
    return {"data": _cmd(db).company_health()}


@router.get("/command/business-intelligence", dependencies=[_read])
def command_bi(db: Session = Depends(get_db)) -> dict:
    """Executive business-intelligence KPIs."""
    return {"data": _cmd(db).business_intelligence()}


@router.get("/command/timeline", dependencies=[_read])
def command_timeline(db: Session = Depends(get_db)) -> dict:
    """One executive company timeline."""
    return {"data": _cmd(db).timeline()}


@router.get("/command/risks", dependencies=[_read])
def command_risks(db: Session = Depends(get_db)) -> dict:
    """Aggregated risk dashboard."""
    return {"data": _cmd(db).risk_dashboard()}


@router.get("/command/opportunities", dependencies=[_read])
def command_opportunities(db: Session = Depends(get_db)) -> dict:
    """Opportunity center — improvements, reuse, growth, hiring."""
    return {"data": _cmd(db).opportunity_center()}


@router.get("/command/search", dependencies=[_read])
def command_search(q: str = "", db: Session = Depends(get_db)) -> dict:
    """Universal executive search."""
    return {"data": _cmd(db).search(q)}


# -- Autonomous Company Operations (AURORA Sprint 08) ------------------------


def _ops(db: Session):
    from app.services.operations import OperationsService

    return OperationsService(db)


@router.get("/operations/queue", dependencies=[_read])
def operations_queue(db: Session = Depends(get_db)) -> dict:
    """The live operation queue — running, queued, blocked, waiting, completed."""
    return {"data": _ops(db).operation_queue()}


@router.get("/operations/autonomous-decisions", dependencies=[_read])
def operations_decisions(db: Session = Depends(get_db)) -> dict:
    """Decisions the company made automatically, with reason and policy level."""
    return {"data": _ops(db).autonomous_decisions()}


@router.get("/operations/policy", dependencies=[_read])
def operations_policy(db: Session = Depends(get_db)) -> dict:
    """The Founder approval policy — three levels and why each applies."""
    return {"data": _ops(db).approval_policy()}


@router.get("/operations/activity", dependencies=[_read])
def operations_activity(db: Session = Depends(get_db)) -> dict:
    """The live company activity stream (business language)."""
    return {"data": _ops(db).activity_stream()}


@router.get("/operations/executive-autonomy", dependencies=[_read])
def operations_executive_autonomy(db: Session = Depends(get_db)) -> dict:
    """Each executive's initiatives, delegations, escalations and improvements."""
    return {"data": _ops(db).executive_autonomy()}


@router.get("/operations/policies", dependencies=[_read])
def operations_policies(db: Session = Depends(get_db)) -> dict:
    """Company operating policies."""
    return {"data": _ops(db).policies()}


@router.get("/operations/escalations", dependencies=[_read])
def operations_escalations(db: Session = Depends(get_db)) -> dict:
    """Escalation center — what needs attention now."""
    return {"data": _ops(db).escalations()}


@router.get("/operations/automation", dependencies=[_read])
def operations_automation(db: Session = Depends(get_db)) -> dict:
    """Automation center — what's automated and the time saved."""
    return {"data": _ops(db).automation()}


@router.get("/operations/trust", dependencies=[_read])
def operations_trust(db: Session = Depends(get_db)) -> dict:
    """Trust dashboard — autonomy, overrides, accuracy, confidence."""
    return {"data": _ops(db).trust()}


# -- Delivery Intelligence & Software Factory (AURORA Sprint 09) -------------


def _factory(db: Session):
    from app.services.software_factory import SoftwareFactoryService

    return SoftwareFactoryService(db)


@router.get("/factory/products", dependencies=[_read])
def factory_products(db: Session = Depends(get_db)) -> dict:
    """The product pipeline — every active product in business terms."""
    return {"data": _factory(db).product_pipeline()}


@router.get("/factory/delivery-pipeline", dependencies=[_read])
def factory_delivery_pipeline(db: Session = Depends(get_db)) -> dict:
    """The nine business delivery stages and what sits in each."""
    return {"data": _factory(db).delivery_pipeline()}


@router.get("/factory/build/{product_id}", dependencies=[_read])
def factory_build(product_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Build intelligence for one product — what, why, who, confidence, impact."""
    return {"data": _factory(db).build_intelligence(product_id)}


@router.get("/factory/quality", dependencies=[_read])
def factory_quality(db: Session = Depends(get_db)) -> dict:
    """Quality center — passing, needing attention, trend, release confidence."""
    return {"data": _factory(db).quality_center()}


@router.get("/factory/releases", dependencies=[_read])
def factory_releases(db: Session = Depends(get_db)) -> dict:
    """Release center — upcoming, completed, delayed, blocked, readiness."""
    return {"data": _factory(db).release_center()}


@router.get("/factory/dependencies", dependencies=[_read])
def factory_dependencies(db: Session = Depends(get_db)) -> dict:
    """Dependency map — products, shared capabilities, reuse, risks, owners."""
    return {"data": _factory(db).dependency_map()}


@router.get("/factory/floor", dependencies=[_read])
def factory_floor(db: Session = Depends(get_db)) -> dict:
    """The live software factory floor — who is doing what, in business terms."""
    return {"data": _factory(db).factory_floor()}


@router.get("/factory/portfolio", dependencies=[_read])
def factory_portfolio(db: Session = Depends(get_db)) -> dict:
    """Portfolio view — products by status and business value delivered."""
    return {"data": _factory(db).portfolio()}
