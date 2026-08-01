"""Phase 1 (WP6) — Founder Project Intake + Autonomous Decomposition.

Proves: a Founder intake objective is analysed by the AI CEO and automatically
decomposed into epics -> sprints -> tasks with REAL AI-employee assignment, in a
plan-awaiting-approval state that does NOT begin implementation. Backward
compatibility of the existing project API is also asserted.
"""


def _create_intake(client):
    return client.post(
        "/api/v1/projects",
        json={
            "code": "PROJ-INTAKE-1",
            "name": "Inventory Module",
            "business_objective": "Give the studio a real-time inventory module",
            "business_problem": "No visibility into stock levels",
            "deliverables": ["Inventory API", "Inventory Dashboard", "Stock Alerts"],
            "constraints": ["Must reuse the existing auth", "No new database engine"],
            "acceptance_criteria": "Founder can view live stock and receive alerts",
            "priority": "high",
            "timeline": "2 sprints",
        },
    )


def test_intake_project_creates_with_objective(client, ai_seeded):
    resp = _create_intake(client)
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["business_objective"].startswith("Give the studio")
    assert data["plan_status"] is None  # not decomposed yet


def test_backward_compatible_minimal_project(client, ai_seeded):
    # The pre-existing minimal create (code + name only) must still work.
    resp = client.post("/api/v1/projects", json={"code": "PLAIN-1", "name": "Plain Project"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["plan_status"] is None


def test_decomposition_produces_epics_sprints_tasks_with_assignees(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    plan = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]

    # Business analysis reasoned by the AI CEO.
    analysis = plan["business_analysis"]
    assert analysis["analyst"]
    assert analysis["vision"]
    assert analysis["risks"]
    assert analysis["success_criteria"]

    # Phase 1: the AI CTO contributes a technical strategy...
    assert analysis["cto"]["strategy"]
    assert analysis["cto"]["stack"]
    # ...and the AI Chief Architect a system design.
    assert analysis["architect"]["design"]
    assert analysis["architect"]["components"]
    assert analysis["architecture_proposal"]  # backward-compatible field

    # Epics and tasks come from the Architect's design, not a fixed template:
    # the counts are whatever the executives decided, not a constant.
    assert plan["totals"]["epics"] >= 1
    assert plan["totals"]["sprints"] == plan["totals"]["epics"]  # one sprint per epic
    assert plan["totals"]["tasks"] >= plan["totals"]["epics"]
    assert plan["totals"]["estimated_hours"] > 0

    # Task titles are product-specific, not the old lifecycle labels.
    titles = [t["title"] for t in plan["tasks"]]
    assert not any(t.startswith("Design & architecture — ") for t in titles)

    # Every task is assigned to a REAL AI employee (not a label).
    assert all(t["assignee"] for t in plan["tasks"])
    roles_used = {t["assignee"] for t in plan["tasks"]}
    assert len(roles_used) >= 2  # work is spread across multiple AI employees

    # Plan awaits approval; implementation has NOT begun.
    assert plan["project"]["plan_status"] == "decomposed"
    assert plan["project"]["status"] == "planning"


def test_decomposition_does_not_start_implementation(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    # No development task/run was triggered by decomposition.
    dev = client.get("/api/v1/development/tasks").json()["data"]
    assert dev == [] or all(t.get("status") == "queued" for t in dev)
    # Tasks are in backlog, not in progress.
    plan = client.get(f"/api/v1/projects/{pid}/plan").json()["data"]
    assert all(t["status"] == "backlog" for t in plan["tasks"])


def test_founder_approves_plan(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    client.post(f"/api/v1/projects/{pid}/decompose")
    approved = client.post(f"/api/v1/projects/{pid}/approve-plan").json()["data"]
    assert approved["project"]["plan_status"] == "approved"


def test_decompose_is_idempotent(client, ai_seeded):
    pid = _create_intake(client).json()["data"]["id"]
    first = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]
    second = client.post(f"/api/v1/projects/{pid}/decompose").json()["data"]
    # Re-running REPLACES the prior plan rather than duplicating it: the second
    # run must not accumulate on top of the first.
    assert first["totals"]["tasks"] == second["totals"]["tasks"]
    assert second["totals"]["tasks"] > 0
