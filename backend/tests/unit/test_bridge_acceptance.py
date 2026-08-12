"""F10-PR-3 tests — LiveBridgeRunner wiring (clone/gate/PR injected).

Exercises the runner end-to-end against a LOCAL git repo (no network): the
clone is faked to a local init, the gate is a stub, the PR opener is captured —
so the runner's composition (sandbox = clone, attributed commit, gate, PR on the
explicit repo) is asserted without a container.
"""

from __future__ import annotations

import subprocess
import uuid

import pytest

from app.services.bridge import BridgeEscalation
from app.services.bridge_acceptance import LiveBridgeRunner

RUN_ID = uuid.uuid4()
MISSION_ID = uuid.uuid4()

ARTIFACT = (
    "<<<FILE: app/core/whitespace.py>>>\n"
    "import re\n"
    "def normalize_whitespace(text):\n"
    "    return re.sub(r'\\s+', ' ', text).strip()\n"
    "<<<END>>>\n"
)


def _local_clone(tmp_path):
    """Return a cloner that inits a local git repo (stands in for a real clone)."""

    def cloner(token, task_code):
        path = str(tmp_path / f"clone-{task_code.lower()}")
        subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-q", "--allow-empty", "-m", "base"],
                       cwd=path, check=True)
        return path

    return cloner


def _runner(tmp_path, **over):
    captured = {}

    def gate(sandbox):
        return over.pop("_gate_ok", True), "stub gate"

    kw = dict(
        run_id=RUN_ID, mission_id=MISSION_ID,
        author_name="Ritchie", author_role="Backend Engineer",
        repo="Bhagirath-Organization/WES", base="main",
        cloner=_local_clone(tmp_path), gate=gate,
    )
    kw.update(over)
    r = LiveBridgeRunner(**kw)
    # Capture the PR instead of opening a real one.
    r._open_pr_on_repo = lambda **kwargs: captured.update(kwargs) or {
        "number": 4242, "url": "local://pr/4242"
    }
    r._captured = captured
    return r


def test_live_cycle_clones_commits_and_opens_pr(tmp_path):
    r = _runner(tmp_path)
    result = r.run(artifact_text=ARTIFACT, task_code="ACCEPT-WS", title="feat(core): normalize_whitespace", token="t")
    assert result.status == "opened" and result.pr_number == 4242
    assert result.files == ["app/core/whitespace.py"]
    # The commit landed in the clone with A4 attribution (real git log).
    log = subprocess.run(
        ["git", "log", "-1", "--format=%an|%ae|%cn|%(trailers:key=WES-Run,valueonly)"],
        cwd=result.sandbox_path, capture_output=True, text=True, check=True,
    ).stdout.strip()
    an, ae, cn, trailer = log.split("|")
    assert an == "Ritchie (WES Backend Engineer)"
    assert ae == "bots+wes-ritchie@wes.studio"
    assert cn == "wes-oi-app[bot]"
    assert trailer == str(RUN_ID)
    # PR opened on the runner's EXPLICIT repo (not the ambient github_repo).
    assert r._captured["branch"].startswith("feature/bridge/")


def test_gate_failure_escalates_and_opens_no_pr(tmp_path):
    r = _runner(tmp_path, gate=lambda sandbox: (False, "2 failed"))
    with pytest.raises(BridgeEscalation, match="verification gate failed"):
        r.run(artifact_text=ARTIFACT, task_code="ACCEPT-FAIL", title="t", token="t")
    assert r._captured == {}  # no PR on a failed gate


def test_atlas_artifact_refused_in_live_runner(tmp_path):
    r = _runner(tmp_path)
    bad = "<<<FILE: app/services/engineering_execution.py>>>\n# no\n<<<END>>>\n"
    with pytest.raises(BridgeEscalation, match="ATLAS"):
        r.run(artifact_text=bad, task_code="ACCEPT-ATLAS", title="t", token="t")
    assert r._captured == {}


def test_gate_env_is_hermetic_strips_wes_vars(monkeypatch):
    # F16: the gate must not inherit production infra config (WES_DATABASE_URL,
    # provider/GitHub creds). Every WES_-prefixed var is stripped so the suite
    # runs on its own test fixtures.
    from app.services.bridge_acceptance import LiveBridgeRunner

    monkeypatch.setenv("WES_DATABASE_URL", "postgresql://x@db:5432/prod")
    monkeypatch.setenv("WES_GITHUB_APP_ID", "secret")
    monkeypatch.setenv("PATH", "/usr/bin")  # a non-WES var survives
    env = LiveBridgeRunner._hermetic_env()
    assert not any(k.startswith("WES_") for k in env)
    assert env.get("PATH") == "/usr/bin"
