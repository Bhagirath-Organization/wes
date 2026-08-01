"""Project ATLAS — Repository Intelligence endpoints (Sprint 01).

The company's business understanding of its repositories. Reuses the existing
technical repository engine; adds the business-asset layer. All responses are
business language — no engineering terminology is required for Founder
understanding. Reads: repo:read (all roles); understanding a repository
(analysis) is repo:write (Founder-authorised). Strictly read-only w.r.t. the
repositories themselves.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.domain.roles import Permission

router = APIRouter(prefix="/repository-intelligence", tags=["repository-intelligence"])
_read = Depends(require_permission(Permission.REPO_READ))
_write = Depends(require_permission(Permission.REPO_WRITE))


def _svc(db: Session):
    from app.services.repository_intelligence import RepositoryIntelligenceService

    return RepositoryIntelligenceService(db)


class UnderstandIn(BaseModel):
    rescan: bool = False
    extract_knowledge: bool = True


class EventIn(BaseModel):
    event_type: str
    repository_id: uuid.UUID | None = None
    detail: str | None = None
    external_ref: str | None = None


# --- discovery ------------------------------------------------------------
@router.get("/discover", dependencies=[_read])
def discover(db: Session = Depends(get_db)) -> dict:
    """Every connected repository, understood as a business asset."""
    return {"data": _svc(db).discover()}


@router.get("/connected", dependencies=[_read])
def connected(db: Session = Depends(get_db)) -> dict:
    """Repositories the company's GitHub App can see (read-only discovery)."""
    return {"data": _svc(db).connected_repositories()}


# --- understanding (analysis) ---------------------------------------------
@router.post("/{repository_id}/understand", dependencies=[_write])
def understand(repository_id: uuid.UUID, payload: UnderstandIn | None = None,
               db: Session = Depends(get_db)) -> dict:
    """Analyse a repository and capture business intelligence (read-only scan)."""
    payload = payload or UnderstandIn()
    return {"data": _svc(db).understand(
        repository_id, rescan=payload.rescan, extract_knowledge=payload.extract_knowledge)}


@router.get("/{repository_id}", dependencies=[_read])
def intelligence(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """The company's business understanding of one repository."""
    return {"data": _svc(db).intelligence(repository_id)}


@router.get("/{repository_id}/architecture", dependencies=[_read])
def architecture(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Architecture intelligence (structured; Founder-safe summary)."""
    return {"data": _svc(db).architecture_intelligence(repository_id)}


@router.get("/{repository_id}/dependencies", dependencies=[_read])
def dependencies(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Dependency intelligence and its business impact."""
    return {"data": _svc(db).dependency_intelligence(repository_id)}


@router.get("/{repository_id}/health", dependencies=[_read])
def health(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Codebase health as business risk & confidence."""
    return {"data": _svc(db).codebase_health(repository_id)}


@router.get("/{repository_id}/blueprint-alignment", dependencies=[_read])
def blueprint_alignment(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """How the repository aligns with the company Blueprint."""
    return {"data": _svc(db).blueprint_alignment(repository_id)}


@router.get("/{repository_id}/ownership", dependencies=[_read])
def ownership(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Executive ownership and responsibilities for this repository."""
    return {"data": _svc(db).executive_ownership(repository_id)}


@router.get("/{repository_id}/memory", dependencies=[_read])
def memory(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """What the company remembers about this repository."""
    return {"data": _svc(db).repository_memory(repository_id)}


# --- graph ----------------------------------------------------------------
@router.get("/graph/all", dependencies=[_read])
def graph_all(db: Session = Depends(get_db)) -> dict:
    """The whole repository graph across all assets."""
    return {"data": _svc(db).graph(None)}


@router.get("/{repository_id}/graph", dependencies=[_read])
def graph_one(repository_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """The structured graph for one repository."""
    return {"data": _svc(db).graph(repository_id)}


# --- events ---------------------------------------------------------------
@router.get("/events/stream", dependencies=[_read])
def events(repository_id: uuid.UUID | None = Query(default=None),
           limit: int = Query(default=50, ge=1, le=200),
           db: Session = Depends(get_db)) -> dict:
    """Engineering activity translated into company (business) events."""
    return {"data": _svc(db).events(repository_id, limit=limit)}


@router.post("/events/ingest", dependencies=[_write])
def ingest(payload: EventIn, db: Session = Depends(get_db)) -> dict:
    """Ingest an engineering event; it is stored as a business-translated event."""
    ev = _svc(db).ingest_event(
        event_type=payload.event_type, repository_id=payload.repository_id,
        detail=payload.detail, source="api", external_ref=payload.external_ref)
    db.commit()
    return {"data": {"business_event": ev.business_event, "category": ev.business_category}}
