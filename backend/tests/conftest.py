"""Pytest fixtures.

Each test runs against a fresh in-memory SQLite database (sanctioned for tests
by Blueprint Vol. 06). A StaticPool keeps a single shared connection so the app
and the test see the same data.
"""

import os

# Disable startup auto-migration/seeding before the app is imported: tests manage
# their own isolated in-memory schema and must not touch the configured database.
os.environ["WES_AUTO_MIGRATE"] = "false"
os.environ["WES_SEED_ON_START"] = "false"
# Isolate autonomous-development git sandboxes to a temp dir for tests.
os.environ.setdefault("WES_DEV_WORKSPACE_DIR", "/tmp/wes-dev-test-workspaces")
os.environ.setdefault("WES_DEVOPS_WORKSPACE_DIR", "/tmp/wes-devops-test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def SessionFactory(engine):
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )


@pytest.fixture
def db_session(SessionFactory) -> Session:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


def _db_override_factory(SessionFactory):
    def _get_db_override():
        db = SessionFactory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return _get_db_override


import uuid  # noqa: E402

from app.api.deps import CurrentUser, get_current_user  # noqa: E402
from app.domain.roles import Role  # noqa: E402


def _principal(role: Role) -> CurrentUser:
    # Deterministic per-role id so a principal is stable across requests within a
    # test (needed for per-user features like knowledge bookmarks).
    return CurrentUser(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"wes-test-{role.value}"),
        email=f"{role.value}@wes.studio",
        role=role,
        full_name=f"Test {role.value}",
        department_id=None,
    )


@pytest.fixture
def client(SessionFactory) -> TestClient:
    """Authenticated client acting as a Founder (full access).

    Existing Company Engine tests use this and continue to pass, now under auth.
    """
    app.dependency_overrides[get_db] = _db_override_factory(SessionFactory)
    app.dependency_overrides[get_current_user] = lambda: _principal(Role.FOUNDER)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def as_role(client):
    """Return a setter that switches the current user's role on the client."""

    def _set(role: Role) -> None:
        app.dependency_overrides[get_current_user] = lambda: _principal(role)

    return _set


@pytest.fixture
def api_client(SessionFactory) -> TestClient:
    """Client WITHOUT an auth override — exercises the real login/JWT flow."""
    app.dependency_overrides[get_db] = _db_override_factory(SessionFactory)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def ai_seeded(SessionFactory):
    """Seed the AI organization (3 depts, 12 roles, 12 employees) into the test DB."""
    from app.db.seed_ai import seed_ai

    db = SessionFactory()
    try:
        seed_ai(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def work_seeded(SessionFactory):
    """Seed the AI org + PROJECT-001 (WORLD) work data into the test DB."""
    from app.db.seed_ai import seed_ai
    from app.db.seed_work import seed_work

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def exec_seeded(SessionFactory):
    """Seed AI org + work + execution engine data into the test DB."""
    from app.db.seed_ai import seed_ai
    from app.db.seed_execution import seed_execution
    from app.db.seed_work import seed_work

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def orch_seeded(SessionFactory):
    """Seed AI org + work + execution + orchestration (providers, sample run)."""
    from app.db.seed_ai import seed_ai
    from app.db.seed_execution import seed_execution
    from app.db.seed_orchestration import seed_orchestration
    from app.db.seed_work import seed_work

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def knowledge_seeded(SessionFactory):
    """Seed AI org + work + execution + orchestration + knowledge into the test DB."""
    from app.db.seed_ai import seed_ai
    from app.db.seed_execution import seed_execution
    from app.db.seed_knowledge import seed_knowledge
    from app.db.seed_orchestration import seed_orchestration
    from app.db.seed_work import seed_work

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.flush()
        seed_knowledge(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def repo_seeded(SessionFactory):
    """Register + scan the WES backend app package into the test DB."""
    from app.db.seed_ai import seed_ai
    from app.db.seed_work import seed_work
    from app.services.repository_service import IndexerService, RepositoryService

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        import os

        repo = RepositoryService(db).register(
            "WES Backend Test", os.path.abspath("app/providers"), slug="wes-test"
        )
        db.flush()
        IndexerService(db).scan(repo.id)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def dev_seeded(SessionFactory):
    """Seed AI org + work + orchestration + knowledge + a scanned repository so
    the autonomous development workflow has full context to plan against."""
    import os

    from app.db.seed_ai import seed_ai
    from app.db.seed_execution import seed_execution
    from app.db.seed_knowledge import seed_knowledge
    from app.db.seed_orchestration import seed_orchestration
    from app.db.seed_work import seed_work
    from app.services.repository_service import IndexerService, RepositoryService

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.flush()
        seed_knowledge(db)
        db.flush()
        repo = RepositoryService(db).register(
            "WES Backend Test", os.path.abspath("app/providers"), slug="wes-dev-test"
        )
        db.flush()
        IndexerService(db).scan(repo.id)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def quality_seeded(SessionFactory):
    """dev_seeded context + the seeded quality-gate rules."""
    import os

    from app.db.seed_ai import seed_ai
    from app.db.seed_execution import seed_execution
    from app.db.seed_knowledge import seed_knowledge
    from app.db.seed_orchestration import seed_orchestration
    from app.db.seed_quality import seed_quality
    from app.db.seed_work import seed_work
    from app.services.repository_service import IndexerService, RepositoryService

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.flush()
        seed_knowledge(db)
        db.flush()
        repo = RepositoryService(db).register(
            "WES Backend Test", os.path.abspath("app/providers"), slug="wes-q-test"
        )
        db.flush()
        IndexerService(db).scan(repo.id)
        db.flush()
        seed_quality(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def devops_seeded(SessionFactory):
    """Full context (quality_seeded) + environment profiles, for the DevOps platform."""
    import os

    from app.db.seed_ai import seed_ai
    from app.db.seed_devops import seed_devops
    from app.db.seed_execution import seed_execution
    from app.db.seed_knowledge import seed_knowledge
    from app.db.seed_orchestration import seed_orchestration
    from app.db.seed_quality import seed_quality
    from app.db.seed_work import seed_work
    from app.services.repository_service import IndexerService, RepositoryService

    db = SessionFactory()
    try:
        seed_ai(db)
        db.flush()
        seed_work(db)
        db.flush()
        seed_execution(db)
        db.flush()
        seed_orchestration(db)
        db.flush()
        seed_knowledge(db)
        db.flush()
        repo = RepositoryService(db).register(
            "WES Backend Test", os.path.abspath("app/providers"), slug="wes-ops-test"
        )
        db.flush()
        IndexerService(db).scan(repo.id)
        db.flush()
        seed_quality(db)
        db.flush()
        seed_devops(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def company(client) -> dict:
    """A persisted company, returned as its API representation."""
    resp = client.post(
        "/api/v1/companies",
        json={
            "name": "WORLD Engineering Studio",
            "slug": "wes",
            "company_type": "Independent AI Engineering Company",
            "purpose": "Build software",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture
def department(client, company) -> dict:
    resp = client.post(
        "/api/v1/departments",
        json={
            "company_id": company["id"],
            "code": "DEPT-02",
            "name": "Engineering",
            "focus": "Build the software",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture(autouse=True)
def stub_executive_reasoning(monkeypatch):
    """Keep the suite hermetic and offline.

    Phase 1 makes the AI CEO / CTO / Chief Architect reason through a live AI
    provider. Unit tests must not depend on a model being installed, so the
    executive chain is stubbed with a deterministic decision that still varies
    with the objective. Real (non-stubbed) reasoning is verified separately
    against the running provider.
    """
    from app.services.executive_reasoning import ExecutiveReasoningService

    def _fake_plan(self, objective, context=""):
        subject = (objective or "the product").strip().rstrip(".")
        return {
            "ceo": {
                "analyst": "AI CEO",
                "vision": f"Deliver {subject} with measurable business value.",
                "scope": {
                    "in_scope": [f"{subject} core capability"],
                    "out_of_scope": ["Unrelated systems"],
                },
                "risks": ["Scope creep", "Integration risk"],
                "success_criteria": [f"Founder can operate {subject} end to end"],
            },
            "cto": {
                "strategist": "AI CTO",
                "strategy": f"Incremental delivery of {subject} on the existing stack.",
                "stack": ["Python", "FastAPI", "PostgreSQL"],
                "key_decisions": ["Reuse the existing auth layer"],
                "technical_risks": ["Data migration effort"],
            },
            "architect": {
                "architect": "AI Chief Architect",
                "design": f"Layered design for {subject}: API -> service -> repository.",
                "components": ["API", "Service", "Repository"],
                "epics": [
                    {
                        "name": f"{subject} core",
                        "tasks": [
                            {"title": f"Model and persist {subject} data", "role": "backend", "hours": 6},
                            {"title": f"Expose {subject} API endpoints", "role": "backend", "hours": 5},
                        ],
                    },
                    {
                        "name": f"{subject} experience",
                        "tasks": [
                            {"title": f"Build the {subject} screen", "role": "frontend", "hours": 6},
                            {"title": f"Verify {subject} flows", "role": "qa", "hours": 4},
                        ],
                    },
                ],
            },
        }

    def _fake_ceo(self, objective, context=""):
        return _fake_plan(self, objective, context)["ceo"]

    def _fake_cto(self, objective, ceo):
        return _fake_plan(self, objective)["cto"]

    def _fake_arch(self, objective, ceo, cto):
        return _fake_plan(self, objective)["architect"]

    monkeypatch.setattr(ExecutiveReasoningService, "executive_plan", _fake_plan)
    monkeypatch.setattr(ExecutiveReasoningService, "ceo_analysis", _fake_ceo)
    monkeypatch.setattr(ExecutiveReasoningService, "cto_strategy", _fake_cto)
    monkeypatch.setattr(ExecutiveReasoningService, "architect_design", _fake_arch)


@pytest.fixture(autouse=True)
def stub_domain_intelligence(monkeypatch):
    """Keep the suite hermetic for Phase B domain understanding.

    ``DomainIntelligenceService.understand`` reasons through a live provider; unit
    tests must not depend on a model. Stub it with a deterministic Business
    Understanding Report that still varies with the objective. Real domain analysis
    is verified separately against the running provider.
    """
    from app.services.domain_intelligence import DomainIntelligenceService

    def _fake_understand(self, objective, *, project_id=None, context=""):
        subject = (objective or "the business").strip().rstrip(".")
        return {
            "industry": f"{subject} industry",
            "business_model": f"Operations for {subject}",
            "daily_operations": [f"Run {subject} daily workflow"],
            "stakeholders": ["Owner", "Staff", "Customer"],
            "user_types": ["Admin", "Operator"],
            "operational_constraints": ["Offline resilience"],
            "compliance": ["Data protection"],
            "business_risks": ["Adoption risk"],
            "kpis": ["Throughput", "Accuracy"],
            "pain_points": ["Manual work"],
            "industry_best_practices": ["Automate the repetitive path"],
            "existing_solutions": ["Spreadsheets"],
            "future_scalability": ["Multi-branch"],
            "departments": ["Operations", "Finance"],
            "roles": ["Manager", "Clerk"],
            "approval_flows": ["Manager approves"],
            "business_events": ["Record created"],
            "master_data": ["Entities"],
            "transactions": ["Daily records"],
            "business_documents": ["Statement"],
            "automation_opportunities": ["Auto-calculation"],
            "suggested_modules": [f"{subject} core"],
            "suggested_dashboards": ["Operations dashboard"],
            "suggested_reports": ["Daily summary"],
            "suggested_kpis": ["Throughput"],
            "roadmap": ["MVP", "Scale"],
            "industry_best_practices_applied": [],
            "reused_industry_knowledge": [],
            "business_confidence": 0.8,
            "analyst": "AI Business Analyst",
        }

    monkeypatch.setattr(DomainIntelligenceService, "understand", _fake_understand)


@pytest.fixture(autouse=True)
def stub_planning_engine(monkeypatch):
    """Keep the suite hermetic for the Phase 2 planning engine.

    The engine's REASONING steps (gap/milestone/sprint/task/risk) call a live AI
    provider; tests stub the composed ``build`` with a deterministic plan that
    still varies with the objective and still flows through the REAL graph
    computation + persistence, so the wiring is exercised offline.
    """
    from app.services.planning_engine import PlanningEngineService

    def _fake_build(self, objective, ceo, cto, architect, constraints=None, memory_context=""):
        subject = (objective or "the product").strip().rstrip(".")
        tasks = [
            {"key": "T1", "title": f"Model and persist {subject} data", "role": "backend",
             "hours": 6, "milestone_key": "M1", "sprint_number": 1,
             "acceptance_criteria": f"A row for {subject} can be created and read back via the API.",
             "definition_of_done": "Migration applied; unit tests pass.",
             "depends_on": [], "reuses": ["auth"]},
            {"key": "T2", "title": f"Expose {subject} REST endpoints", "role": "backend",
             "hours": 5, "milestone_key": "M1", "sprint_number": 1,
             "acceptance_criteria": f"GET/POST /{subject} return 200/201 with the expected shape.",
             "definition_of_done": "Endpoints covered by tests.",
             "depends_on": ["T1"], "reuses": []},
            {"key": "T3", "title": f"Build the {subject} screen", "role": "frontend",
             "hours": 6, "milestone_key": "M2", "sprint_number": 2,
             "acceptance_criteria": f"The {subject} screen lists and creates records.",
             "definition_of_done": "Screen renders; component test passes.",
             "depends_on": ["T2"], "reuses": []},
            {"key": "T4", "title": f"Verify {subject} flows", "role": "qa",
             "hours": 4, "milestone_key": "M2", "sprint_number": 2,
             "acceptance_criteria": f"End-to-end {subject} create/read flow passes.",
             "definition_of_done": "QA sign-off recorded.",
             "depends_on": ["T2", "T3"], "reuses": []},
        ]
        return {
            "repository_analysis": {"repository": "WES Backend", "modules": ["auth", "jobs"],
                                    "layers": ["api", "service"], "dependencies": ["fastapi"], "known": True},
            "gap_analysis": {"reuse": [{"component": "auth", "why": "already implemented"}],
                             "missing": [f"{subject} domain model"], "duplication_risks": ["auth"]},
            "milestones": [
                {"key": "M1", "name": f"{subject} core", "business_objective": f"Deliver {subject} data + API",
                 "deliverables": [f"{subject} API"], "acceptance_criteria": f"{subject} API is live",
                 "definition_of_done": "API tested + reviewed", "review_trigger": "on merge", "depends_on": []},
                {"key": "M2", "name": f"{subject} experience", "business_objective": f"Deliver {subject} UI",
                 "deliverables": [f"{subject} screen"], "acceptance_criteria": f"{subject} screen usable",
                 "definition_of_done": "UI tested", "review_trigger": "on merge", "depends_on": ["M1"]},
            ],
            "sprints": [
                {"number": 1, "objective": f"Build {subject} backend", "capacity_hours": 40,
                 "exit_criteria": "API green", "risk_level": "medium", "milestone_key": "M1"},
                {"number": 2, "objective": f"Build {subject} frontend", "capacity_hours": 40,
                 "exit_criteria": "UI green", "risk_level": "low", "milestone_key": "M2"},
            ],
            "tasks": tasks,
            "risks": [
                {"title": f"Integration risk for {subject}", "category": "integration",
                 "probability": "medium", "impact": "high",
                 "mitigation": "Reuse existing auth and validate contracts", "owner_role": "architect"},
            ],
            "graph": PlanningEngineService.compute_graph(tasks),
            "definition_of_done": {"project": f"{subject} milestones all meet DoD and Founder approves."},
        }

    monkeypatch.setattr(PlanningEngineService, "build", _fake_build)


@pytest.fixture(autouse=True)
def stub_collaboration(monkeypatch):
    """Keep the suite hermetic for Phase 3 collaboration.

    decompose() now runs a real multi-agent discussion (executive_consensus) and a
    review_chain — both call the live provider. Tests stub them with deterministic,
    objective-varying outcomes; the REAL persistence path (project_conversations
    read) is left intact. Live collaboration is verified separately.
    """
    from app.services.collaboration import CollaborationService
    from app.domain.orchestration_enums import CollaborationType

    def _consensus(self, project, ceo, cto):
        subject = (project.business_objective or project.name or "the product").strip().rstrip(".")
        th = self.open_thread(project.id, f"Executive consensus — {project.name}", "executive_consensus")
        emp = self._emp("CEO")
        cto_e = self._emp("CTO", "CHIEF_ARCHITECT")
        self.say(th, emp, CollaborationType.QUESTION, f"How do we de-risk {subject}?", to=cto_e)
        self.say(th, cto_e, CollaborationType.ANSWER, f"Deliver {subject} incrementally.", to=emp)
        self.say(th, emp, CollaborationType.APPROVAL, f"Approved direction for {subject}.", to=cto_e)
        th.status = "resolved"; self.db.flush()
        return {"thread_id": str(th.id), "decision": "approved", "rationale": "sound",
                "agreed_constraints": [f"reuse existing auth for {subject}"], "open_concerns": [],
                "cto_agreed": True, "architect_position": "endorse", "turns": self._seq}

    def _review(self, project, plan_summary):
        th = self.open_thread(project.id, f"Plan review — {project.name}", "plan_review")
        sec = self._emp("SECURITY_ENGINEER"); qa = self._emp("QA_ENGINEER")
        self.say(th, sec, CollaborationType.APPROVAL, "[approved] security ok", to=qa)
        self.say(th, qa, CollaborationType.APPROVAL, "[approved] testable", to=sec)
        th.status = "resolved"; self.db.flush()
        return {"thread_id": str(th.id), "approved": True,
                "reviews": [{"reviewer": "Security Engineer AI", "verdict": "approved", "findings": [], "required_changes": []},
                            {"reviewer": "QA Engineer AI", "verdict": "approved", "findings": [], "required_changes": []}],
                "turns": self._seq}

    monkeypatch.setattr(CollaborationService, "executive_consensus", _consensus)
    monkeypatch.setattr(CollaborationService, "review_chain", _review)


@pytest.fixture(autouse=True)
def stub_company_memory(monkeypatch):
    """Keep the suite hermetic for Phase 4 memory.

    decompose() now records/recalls company memory. The write path (remember /
    capture_project / project_memory) is REAL and exercised (it persists rows);
    only the network-bound pieces are stubbed: embeddings return None (keyword
    fallback), the LLM retrospective is not called in decompose, and repetition
    mining is left real. This keeps tests offline while still exercising the
    persistence + graph wiring.
    """
    from app.services.embedding import EmbeddingService

    monkeypatch.setattr(EmbeddingService, "embed", lambda self, text: None)
    monkeypatch.setattr(EmbeddingService, "available", lambda self: False)


@pytest.fixture(autouse=True)
def stub_autonomous_engineering(monkeypatch):
    """Keep the suite hermetic for Phase 5 autonomous engineering.

    run_workflow now runs a self-debug loop and a 4-reviewer board (real provider
    calls). Tests stub them deterministically; the workflow wiring, sessions and
    merge-readiness aggregation are still exercised. Live behaviour is verified
    separately.
    """
    from app.services.autonomous_engineering import AutonomousEngineeringService as A

    monkeypatch.setattr(A, "engineering_context", lambda self, title, description=None: "")
    monkeypatch.setattr(
        A, "self_debug",
        lambda self, *, task, sandbox, git, changes, provider_name=None, max_iterations=2: {
            "resolved": True,
            "iterations": [{"iteration": 0, "passed": 1, "failed": 0, "action": "green"}],
        },
    )
    monkeypatch.setattr(
        A, "review_board",
        lambda self, task, diff: {
            "approved": True,
            "reviews": [
                {"reviewer": r, "role": r, "dimension": r, "verdict": "approved",
                 "score": 90, "findings": [], "required_changes": []}
                for r in ("AI Chief Architect", "AI QA Engineer", "AI Security Engineer", "AI Performance Reviewer")
            ],
            "blocking": [],
        },
    )
