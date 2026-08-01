"""Project ATLAS — Repository Intelligence Engine tests (Sprint 01).

Exercises the business-asset layer over the existing repository engine:
discovery, understanding, architecture/dependency/health intelligence, executive
ownership, Blueprint alignment, the repository graph, knowledge extraction into
the Company Brain, and business-translated events. Reuses the ``repo_seeded``
fixture (a real scan of ``app/providers``). Read-only w.r.t. repositories.
"""


def _repo_id(client):
    return client.get("/api/v1/repositories").json()["data"][0]["id"]


def _understand(client, rid):
    resp = client.post(f"/api/v1/repository-intelligence/{rid}/understand", json={})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


# --- discovery ------------------------------------------------------------
def test_discover_lists_assets(client, repo_seeded):
    data = client.get("/api/v1/repository-intelligence/discover").json()["data"]
    assert data["total"] >= 1
    asset = data["assets"][0]
    assert "name" in asset and "business_status" in asset and "repository_health" in asset
    # discovery before understanding => "new"
    assert asset["business_status"] in ("new", "understood", "active")


def test_connected_is_safe_without_github(client, repo_seeded):
    # No GitHub App configured in tests → returns registered-only, never errors.
    data = client.get("/api/v1/repository-intelligence/connected").json()["data"]
    assert "connected" in data and "registered_count" in data
    assert data["registered_count"] >= 1


# --- understanding --------------------------------------------------------
def test_understand_captures_business_intelligence(client, repo_seeded):
    rid = _repo_id(client)
    intel = _understand(client, rid)
    assert intel["understood"] is True
    assert intel["business_capability"]
    assert intel["architecture_style"]
    assert 0 <= intel["health_score"] <= 100
    assert 0 <= intel["confidence"] <= 100
    assert intel["executive_owner"] in (
        "Chief Executive", "Chief Architect", "Engineering Director")
    assert intel["risk_level"] in ("low", "moderate", "elevated", "high")


def test_understand_is_idempotent(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    again = _understand(client, rid)  # second pass must not error or duplicate
    assert again["understood"] is True
    # discovery now reports it understood
    assets = client.get("/api/v1/repository-intelligence/discover").json()["data"]["assets"]
    assert any(a["business_status"] != "new" for a in assets)


def test_architecture_intelligence(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    arch = client.get(f"/api/v1/repository-intelligence/{rid}/architecture").json()["data"]
    assert "layer_structure" in arch
    assert "data_flow" in arch
    assert "module_boundaries" in arch


def test_dependency_intelligence(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    dep = client.get(f"/api/v1/repository-intelligence/{rid}/dependencies").json()["data"]
    assert "external_services" in dep
    assert "business_impact" in dep
    assert isinstance(dep["reusable_modules"], list)


def test_codebase_health(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    health = client.get(f"/api/v1/repository-intelligence/{rid}/health").json()["data"]
    assert 0 <= health["health_score"] <= 100
    assert health["risk_level"] in ("low", "moderate", "elevated", "high")
    assert "business_risk" in health


def test_blueprint_alignment(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    bp = client.get(f"/api/v1/repository-intelligence/{rid}/blueprint-alignment").json()["data"]
    assert 0 <= bp["coverage"] <= 100
    assert "recommendations" in bp
    assert "compliance" in bp


def test_executive_ownership(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    own = client.get(f"/api/v1/repository-intelligence/{rid}/ownership").json()["data"]
    execs = {o["executive"] for o in own["owners"]}
    assert {"Chief Executive", "Chief Architect", "Engineering Director",
            "QA Director", "Security Director", "Business Analyst"} <= execs


def test_repository_memory(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    mem = client.get(f"/api/v1/repository-intelligence/{rid}/memory").json()["data"]
    assert "reusable_modules" in mem
    assert "known_issues" in mem
    assert "learning_history" in mem


# --- graph ----------------------------------------------------------------
def test_repository_graph_has_levels_and_edges(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    graph = client.get(f"/api/v1/repository-intelligence/{rid}/graph").json()["data"]
    types = {n["type"] for n in graph["nodes"]}
    assert "repository" in types
    assert "executive" in types
    assert any(e["relation"] == "owned_by" for e in graph["edges"])
    # graph levels reflect the required hierarchy
    assert graph["levels"][0] == "repository"


# --- knowledge extraction into Company Brain ------------------------------
def test_knowledge_extracted_into_company_brain(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)
    # a knowledge document linked to the repository must now exist
    docs = client.get("/api/v1/knowledge/documents").json()["data"]
    titles = " ".join(d.get("title", "") for d in docs)
    assert "Repository Intelligence" in titles


# --- events + business translation ----------------------------------------
def test_events_are_business_translated(client, repo_seeded):
    rid = _repo_id(client)
    _understand(client, rid)  # emits a repository_analysed event
    data = client.get("/api/v1/repository-intelligence/events/stream").json()["data"]
    assert data["total"] >= 1
    ev = data["events"][0]
    assert ev["business_event"]
    # no engineering terminology leaks into the business event text
    lowered = ev["business_event"].lower()
    for banned in ("commit", "branch", "merge pr", "pull request", "ci ", "container"):
        assert banned not in lowered


def test_event_ingestion_translates_engineering_to_business(client, repo_seeded):
    rid = _repo_id(client)
    resp = client.post("/api/v1/repository-intelligence/events/ingest",
                       json={"event_type": "merge", "repository_id": rid})
    assert resp.status_code == 200, resp.text
    out = resp.json()["data"]
    assert out["business_event"] == "Engineering completed a business capability."
    assert out["category"] == "delivery"


def test_translation_layer_covers_all_event_types():
    from app.services.repository_intelligence import RepositoryIntelligenceService as S

    for et, expected_business in [
        ("repository_created", "connected"),
        ("release", "product version"),
        ("pull_request", "review"),
        ("issue", "improvement"),
    ]:
        business, category = S.translate_event(et)
        assert expected_business in business.lower()
        assert category


# --- security: read-only ---------------------------------------------------
def test_understand_requires_founder(client, as_role, repo_seeded):
    from app.domain.roles import Role

    rid = _repo_id(client)
    as_role(Role.READ_ONLY)
    resp = client.post(f"/api/v1/repository-intelligence/{rid}/understand", json={})
    assert resp.status_code == 403


def test_reads_allowed_for_all_roles(client, as_role, repo_seeded):
    from app.domain.roles import Role

    as_role(Role.READ_ONLY)
    resp = client.get("/api/v1/repository-intelligence/discover")
    assert resp.status_code == 200
