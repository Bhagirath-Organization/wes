"""B6 merge-detection tests — the five properties the Founder pinned.

Each of the Founder's five requirements has a dedicated, asserted test:
poll/catch-up, idempotent firing, bridge-only scope (refusal), App-token identity
(no new credential), and Postgres-parity (no new value-shape written).
"""

from __future__ import annotations

from app.domain.development_enums import DevTaskStatus
from app.domain.work_enums import ProjectStatus, WorkStatus
from app.models.development import DevelopmentTask
from app.models.work import Project, WorkItem
from app.services.merge_detection import (
    BridgeMergeDetector,
    detect_and_advance_bridge_merges,
)

# -- fixtures (same shape as test_bridge_lifecycle) --------------------------


def _project(db, code="P-1", status=ProjectStatus.PLANNING):
    p = Project(code=code, name=code, status=status)
    db.add(p)
    db.flush()
    return p


def _item(db, project, code, status=WorkStatus.IN_PROGRESS):
    w = WorkItem(project_id=project.id, task_code=code, title=code, status=status)
    db.add(w)
    db.flush()
    return w


def _dev(db, wi, code, status=DevTaskStatus.PR_READY):
    d = DevelopmentTask(code=code, title=code, status=status, work_item_id=wi.id)
    db.add(d)
    db.flush()
    return d


def _pr(number, head_ref, *, merged=True):
    return {
        "number": number,
        "head": {"ref": head_ref},
        "base": {"ref": "main"},
        "merged_at": "2026-08-12T10:00:00Z" if merged else None,
    }


class _FakeGH:
    """Stands in for GitHubService.list_pulls (App-token read) in tests."""

    def __init__(self, pulls):
        self._pulls = pulls
        self.calls = []

    def list_pulls(self, *, state="closed", base=None):
        self.calls.append((state, base))
        return self._pulls


# -- POINT 1: poll + catch-up ------------------------------------------------


def test_detects_and_advances_a_merged_bridge_pr(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T1")
    dev = _dev(db_session, wi, "DEV-A")
    gh = _FakeGH([_pr(30, "feature/bridge/dev-a")])
    out = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert out["advanced"] == ["DEV-A"] and out["scanned"] == 1
    assert dev.status == DevTaskStatus.MERGED
    assert wi.status == WorkStatus.DONE
    assert db_session.get(Project, p.id).status == ProjectStatus.COMPLETED


def test_catch_up_advances_a_merge_that_happened_while_detector_was_down(db_session):
    # The pass reconciles GitHub's CURRENT merged state against the DB — it does
    # not consume a live event — so a PR merged before the detector ran is still
    # caught: the task is pr_ready, the PR reports merged, the pass advances it.
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T2")
    dev = _dev(db_session, wi, "DEV-LATE", status=DevTaskStatus.PR_READY)
    gh = _FakeGH([_pr(31, "feature/bridge/dev-late")])  # merged "in the past"
    out = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert out["advanced"] == ["DEV-LATE"]
    assert dev.status == DevTaskStatus.MERGED


def test_closed_but_not_merged_pr_never_advances(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T3")
    dev = _dev(db_session, wi, "DEV-CLOSED")
    gh = _FakeGH([_pr(32, "feature/bridge/dev-closed", merged=False)])
    out = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert out["scanned"] == 0 and out["advanced"] == []
    assert dev.status == DevTaskStatus.PR_READY  # untouched


def test_merged_bridge_branch_with_no_task_is_skipped_not_errored(db_session):
    gh = _FakeGH([_pr(33, "feature/bridge/ghost-task")])
    out = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert out["no_task"] == ["feature/bridge/ghost-task"]
    assert out["advanced"] == []


# -- POINT 2: idempotent firing ----------------------------------------------


def test_double_detection_does_not_double_advance(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-T4")
    dev = _dev(db_session, wi, "DEV-IDEM")
    gh = _FakeGH([_pr(34, "feature/bridge/dev-idem")])
    first = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    second = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert first["advanced"] == ["DEV-IDEM"]
    # Second pass: no advance — the task is already merged (reported, not re-fired).
    assert second["advanced"] == [] and second["already"] == ["DEV-IDEM"]
    assert dev.status == DevTaskStatus.MERGED
    assert wi.status == WorkStatus.DONE
    assert db_session.get(Project, p.id).status == ProjectStatus.COMPLETED


# -- POINT 3: scope = bridge PRs only (refusal) ------------------------------


def test_governed_non_bridge_pr_never_auto_advances(db_session):
    # A merged governed PR (fix/*) MUST NOT advance anything — even when a task
    # with the matching code exists. Only feature/bridge/* may ever fire.
    p = _project(db_session)
    wi_gov = _item(db_session, p, "P1-GOV")
    dev_gov = _dev(db_session, wi_gov, "DEV-GOV")
    wi_br = _item(db_session, p, "P1-BR")
    dev_br = _dev(db_session, wi_br, "DEV-BR")
    gh = _FakeGH([
        _pr(35, "fix/dev-gov"),            # governed — must be ignored
        _pr(36, "docs/dev-gov"),           # governed — must be ignored
        _pr(37, "feature/bridge/dev-br"),  # bridge — must fire
    ])
    out = detect_and_advance_bridge_merges(db_session, gh, commit=False)
    assert out["non_bridge"] == 2
    assert out["advanced"] == ["DEV-BR"]
    assert dev_gov.status == DevTaskStatus.PR_READY  # governed PR did NOT advance it
    assert dev_br.status == DevTaskStatus.MERGED


# -- POINT 4: identity = App-token read scope, no new credential --------------


def test_detector_uses_github_app_service_no_new_credential():
    from app.services.github_service import GitHubService

    # No injected client -> the detector reaches for the App-authenticated service
    # (the same installation token the bridge uses); it constructs no new secret.
    detector = BridgeMergeDetector(session_factory=lambda: None)
    assert isinstance(detector._client(), GitHubService)
    # An injected read client is honored verbatim (used by run_once/tests).
    fake = _FakeGH([])
    assert BridgeMergeDetector(session_factory=lambda: None, gh=fake)._client() is fake


def test_run_once_reconciles_via_injected_read_client(db_session):
    p = _project(db_session)
    wi = _item(db_session, p, "P1-RO")
    dev = _dev(db_session, wi, "DEV-RO")
    gh = _FakeGH([_pr(38, "feature/bridge/dev-ro")])
    detector = BridgeMergeDetector(session_factory=lambda: db_session, gh=gh)
    out = detector.run_once()
    assert out["advanced"] == ["DEV-RO"]
    assert gh.calls and gh.calls[0][0] == "closed"  # read-only list, closed PRs
    assert dev.status == DevTaskStatus.MERGED


# -- POINT 5: Postgres-parity — no new value-shape written --------------------


def test_only_existing_enum_values_are_written_no_new_shape(db_session):
    # The detector writes ONLY pre-existing enum transitions already exercised on
    # Postgres; there is no new varchar/width surface (F15). Assert the written
    # values are members of their enums and comfortably within column widths.
    p = _project(db_session)
    wi = _item(db_session, p, "P1-PP")
    dev = _dev(db_session, wi, "DEV-PP")
    detect_and_advance_bridge_merges(
        db_session, _FakeGH([_pr(39, "feature/bridge/dev-pp")]), commit=False
    )
    assert dev.status in set(DevTaskStatus)
    assert wi.status in set(WorkStatus)
    assert db_session.get(Project, p.id).status in set(ProjectStatus)
    # widths: status columns are String(30)/String(20); written values are short.
    assert len(dev.status.value) <= 30 and len(wi.status.value) <= 20


# -- the read method: App-token GET /pulls, read-only --------------------------


def test_list_pulls_is_read_only_and_builds_the_right_query(monkeypatch):
    from app.services import github_service as gs

    class _FakeResp:
        status_code = 200
        content = b"x"

        class request:  # noqa: N801 - mimic httpx.Response.request.method
            method = "GET"

        class url:  # noqa: N801 - mimic httpx.Response.url.path
            path = "/repos/o/r/pulls"

        def json(self):
            return [{"number": 1, "head": {"ref": "feature/bridge/x"}, "merged_at": "t"}]

    monkeypatch.setattr(gs.GitHubService, "configured", staticmethod(lambda: True))
    captured = {}

    def _fake_request(self, method, path, *, json=None):
        captured["method"], captured["path"] = method, path
        return _FakeResp()

    monkeypatch.setattr(gs.GitHubService, "_request", _fake_request)
    out = gs.GitHubService(repo="o/r").list_pulls(state="closed", base="main")
    assert out and out[0]["number"] == 1
    assert captured["method"] == "GET"  # read-only
    assert "/repos/o/r/pulls" in captured["path"]
    assert "state=closed" in captured["path"] and "base=main" in captured["path"]
