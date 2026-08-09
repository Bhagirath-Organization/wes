"""Project REST endpoints (Sprint 07)."""

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_db, get_work_service, pagination, require_permission
from app.domain.roles import Permission
from app.schemas.work import ProjectCreate, ProjectUpdate
from app.services.project_decomposition import DecompositionService
from app.services.work import WorkService

router = APIRouter(prefix="/projects", tags=["projects"])
_read = Depends(require_permission(Permission.WORK_READ))
_write = Depends(require_permission(Permission.WORK_WRITE))


@router.get("", dependencies=[_read])
def list_projects(
    page: Pagination = Depends(pagination), service: WorkService = Depends(get_work_service)
) -> dict:
    items, total = service.list_projects(offset=page.offset, limit=page.limit)
    return {"data": items, "meta": {"total": total}}


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[_write])
def create_project(
    payload: ProjectCreate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.create_project(payload)}


@router.get("/{project_id}", dependencies=[_read])
def get_project(project_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> dict:
    return {"data": service.get_project(project_id)}


@router.patch("/{project_id}", dependencies=[_write])
def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, service: WorkService = Depends(get_work_service)
) -> dict:
    return {"data": service.update_project(project_id, payload)}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_write])
def delete_project(project_id: uuid.UUID, service: WorkService = Depends(get_work_service)) -> None:
    service.delete_project(project_id)


@router.get("/{project_id}/milestones", dependencies=[_read])
def project_milestones(
    project_id: uuid.UUID, service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_milestones(project_id)
    return {"data": items, "meta": {"total": len(items)}}


@router.get("/{project_id}/sprints", dependencies=[_read])
def project_sprints(
    project_id: uuid.UUID, service: WorkService = Depends(get_work_service)
) -> dict:
    items = service.list_sprints(project_id)
    return {"data": items, "meta": {"total": len(items)}}


# -- Autonomous decomposition (WP6) ---------------------------------------


@router.post("/{project_id}/decompose", dependencies=[_write])
def decompose_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """AI-CEO business analysis + automatic decomposition into epics -> sprints ->
    tasks with AI-employee assignment. Produces a plan awaiting Founder approval;
    does NOT begin implementation.

    NOTE: synchronous — planning runs local CPU inference and can take many
    minutes. Prefer ``/decompose-async`` for the UI so the request never blocks.
    """
    return {"data": DecompositionService(db).decompose(project_id)}


@router.post("/{project_id}/decompose-async", dependencies=[_write], status_code=status.HTTP_202_ACCEPTED)
def decompose_project_async(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Start planning in the background and return immediately.

    Marks the project ``plan_status='planning'`` and enqueues the durable
    ``project_decompose`` job. The UI polls ``GET /projects/{id}`` and renders the
    plan once ``plan_status`` becomes ``decomposed`` (or shows the error on
    ``failed``). This is what makes the Founder page load instantly instead of
    holding a multi-minute request open.
    """
    from app.core.exceptions import NotFoundError, ValidationError
    from app.models.work import Project
    from app.services.job_queue import JobQueue

    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"Project {project_id} not found")
    if project.plan_status == "planning":
        return {"data": {"project_id": str(project_id), "plan_status": "planning",
                         "message": "planning already in progress"}}
    if project.plan_status in ("decomposed", "approved"):
        raise ValidationError(f"Project already planned (plan_status={project.plan_status}).")
    project.plan_status = "planning"
    project.plan_error = None
    db.flush()
    JobQueue(db).enqueue(
        "project_decompose", {"project_id": str(project_id)},
        idempotency_key=f"decompose:{project_id}",
    )
    db.commit()
    return {"data": {"project_id": str(project_id), "plan_status": "planning",
                    "message": "AI CEO is analysing the objective in the background"}}


@router.get("/{project_id}/plan", dependencies=[_read])
def project_plan(project_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return {"data": DecompositionService(db).plan(project_id)}


class ApprovePlanIn(BaseModel):
    """Optional single-approval payload (WES-DEC-011): plan + budget in one act."""

    approved_budget: float | None = None


@router.post("/{project_id}/approve-plan", dependencies=[_write])
def approve_project_plan(
    project_id: uuid.UUID,
    payload: ApprovePlanIn | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """Founder approval of the decomposition plan (unlocks execution phases).

    With ``approved_budget`` this is the WES-DEC-011 single approval: the plan
    AND its mission budget envelope are approved together; execution then runs
    freely inside the envelope (80% notify, 100% hard-stop + escalation).
    """
    data = DecompositionService(db).approve_plan(project_id)
    if payload is not None and payload.approved_budget is not None:
        from app.services.mission_budget import MissionBudgetService

        env = MissionBudgetService(db).approve(project_id, payload.approved_budget)
        db.commit()
        data["budget_envelope"] = {
            "amount": env.max_cost,
            "warning_threshold": env.warning_threshold,
            "hard_stop": env.hard_stop,
        }
    return {"data": data}
