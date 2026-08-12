"""F10-PR-1 bridge-core tests (design decisions A1-a/A2-a/A3-a/A4 + §C-2 rules).

Every §C-2 sandbox hard rule has a refusal-path test (asserted, not assumed);
A4's commit-attribution format is pinned by reading the REAL git log of a
bridge-authored commit in a local sandbox repo. No network, no GitHub — the PR
opener and gate are injected per the design's testability note.
"""

from __future__ import annotations

import subprocess
import uuid

import pytest

from app.services.bridge import (
    ATLAS_DENYLIST,
    BRANCH_PREFIX,
    BridgeEscalation,
    ExecutionPRBridge,
)

RUN_ID = uuid.UUID("7aa4d3a7-eb1f-4371-8ac0-d77bdfd7d8c6")
MISSION_ID = uuid.UUID("f61b198c-e30e-4540-bb82-0a90221f9551")

GOOD_ARTIFACT = (
    "Implementation follows.\n"
    "<<<FILE: app/core/blank.py>>>\n"
    "def is_blank(text: str) -> bool:\n"
    "    return not text.strip()\n"
    "<<<END>>>\n"
    "<<<FILE: tests/unit/test_blank.py>>>\n"
    "from app.core.blank import is_blank\n"
    "def test_blank():\n"
    "    assert is_blank('  ') and not is_blank('x')\n"
    "<<<END>>>\n"
)


class _Workspace:
    """Local sandbox factory (no DevWorkspace base-path config needed)."""

    def __init__(self, tmp_path):
        self.tmp = tmp_path

    def create(self, task_code: str) -> str:
        p = self.tmp / f"sandbox-{task_code.lower()}"
        p.mkdir()
        return str(p)


def _bridge(tmp_path, **over):
    kw = dict(
        run_id=RUN_ID,
        mission_id=MISSION_ID,
        author_name="Ritchie",
        author_role="Backend Engineer",
        gate=lambda sandbox: (True, "gate stub: pass"),
        pr_opener=lambda **kwargs: {"number": 999, "url": "local://pr/999"},
        workspace=_Workspace(tmp_path),
    )
    kw.update(over)
    return ExecutionPRBridge(**kw)


def _git_log(sandbox: str, fmt: str) -> str:
    out = subprocess.run(
        ["git", "log", "-1", f"--format={fmt}"], cwd=sandbox,
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


# --- happy path + A4 attribution pins ---------------------------------------


def test_happy_path_opens_pr_with_attributed_commit(tmp_path):
    result = _bridge(tmp_path).run(
        artifact_text=GOOD_ARTIFACT, task_code="R2-BRIDGE-T1", title="feat(core): is_blank()"
    )
    assert result.status == "opened"
    assert result.branch == f"{BRANCH_PREFIX}r2-bridge-t1"
    assert result.pr_number == 999 and result.files == [
        "app/core/blank.py", "tests/unit/test_blank.py"
    ]
    sandbox = result.sandbox_path
    # A4: author = AI employee, committer = App identity — pinned from real git log.
    assert _git_log(sandbox, "%an") == "Ritchie (WES Backend Engineer)"
    assert _git_log(sandbox, "%ae") == "bots+wes-ritchie@wes.studio"
    assert _git_log(sandbox, "%cn") == "wes-oi-app[bot]"
    assert _git_log(sandbox, "%ce") == "wes-oi-app[bot]@users.noreply.github.com"
    # A4: both machine-parseable trailers present.
    body = _git_log(sandbox, "%B")
    assert f"WES-Run: {RUN_ID}" in body
    assert f"WES-Mission: {MISSION_ID}" in body


def test_trailers_parse_as_git_trailers(tmp_path):
    result = _bridge(tmp_path).run(
        artifact_text=GOOD_ARTIFACT, task_code="R2-BRIDGE-T2", title="feat: t2"
    )
    trailers = subprocess.run(
        ["git", "log", "-1", "--format=%(trailers:key=WES-Run,valueonly)"],
        cwd=result.sandbox_path, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert trailers == str(RUN_ID)  # machine-parseable, not just grep-able


# --- §C-2 rule 1: never the live working tree --------------------------------


def test_rule1_sandbox_inside_live_tree_refused(tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "bridge_live_tree_guard", str(tmp_path))
    with pytest.raises(BridgeEscalation, match="live working tree"):
        _bridge(tmp_path).run(
            artifact_text=GOOD_ARTIFACT, task_code="LIVE-T", title="t"
        )


# --- §C-2 rule 2: never ATLAS files ------------------------------------------


@pytest.mark.parametrize("atlas_path", [
    "app/services/execution_planning.py",
    "backend/alembic/versions/0031_autonomous_engineering_atlas.py",
    ".s5.txt",
])
def test_rule2_atlas_paths_refused_before_any_write(tmp_path, atlas_path):
    artifact = f"<<<FILE: {atlas_path}>>>\n# nope\n<<<END>>>\n"
    bridge = _bridge(tmp_path)
    with pytest.raises(BridgeEscalation, match="ATLAS"):
        bridge.run(artifact_text=artifact, task_code="ATLAS-T", title="t")
    # Refused at parse — no sandbox dir was even created for a write.
    assert not any(p.name.startswith("sandbox-atlas") for p in tmp_path.iterdir())


def test_rule2_denylist_covers_all_standing_ruling_files():
    assert len(ATLAS_DENYLIST) == 8  # the enumerated ATLAS set from the design


# --- §C-2 rule 3: never force-push -------------------------------------------


def test_rule3_no_force_flag_exists_in_the_lane():
    import inspect

    import app.services.bridge as bridge_mod
    from app.services import dev_git

    for mod in (bridge_mod, dev_git):
        src = inspect.getsource(mod)
        assert "--force" not in src and "force-push" not in src.replace(
            "never force-push", ""
        ), f"force flag found in {mod.__name__}"


# --- §C-2 rule 4: never push main --------------------------------------------


def test_rule4_gitservice_refuses_main_push(tmp_path):
    from app.services.dev_git import GitService, SandboxError

    sandbox = _Workspace(tmp_path).create("MAIN-T")
    git = GitService(sandbox)
    git.init()
    with pytest.raises(SandboxError, match="Refusing to push"):
        git.push_via_app("tok", "owner/repo", "main")


def test_rule4_bridge_pins_bridge_prefix(tmp_path):
    # Any branch the bridge produces starts with feature/bridge/ — pinned constant.
    result = _bridge(tmp_path).run(
        artifact_text=GOOD_ARTIFACT, task_code="PREFIX-T", title="t"
    )
    assert result.branch.startswith("feature/bridge/")


# --- §C-2 rule 5: sandbox failure preserved as evidence -----------------------


def test_rule5_failed_gate_preserves_sandbox(tmp_path):
    import os

    bridge = _bridge(tmp_path, gate=lambda sandbox: (False, "3 tests failed"))
    with pytest.raises(BridgeEscalation) as exc:
        bridge.run(artifact_text=GOOD_ARTIFACT, task_code="GATE-T", title="t")
    # The escalation names the preserved path, and the path still exists with
    # the applied change intact — evidence, not cleanup.
    assert "sandbox preserved" in exc.value.escalation
    preserved = [p for p in tmp_path.iterdir() if p.name == "sandbox-gate-t"]
    assert len(preserved) == 1
    assert os.path.isfile(preserved[0] / "app" / "core" / "blank.py")


# --- §C-2 rule 6: no LLM-repair loop — escalate, never guess ------------------


def test_rule6_unparseable_artifact_escalates_with_six_fields(tmp_path):
    calls = {"n": 0}
    bridge = _bridge(tmp_path)
    original = bridge.parse_artifact

    def counting_parse(text):
        calls["n"] += 1
        return original(text)

    bridge.parse_artifact = counting_parse
    with pytest.raises(BridgeEscalation) as exc:
        bridge.run(artifact_text="prose only, no file blocks", task_code="ESC-T", title="t")
    assert calls["n"] == 1  # exactly one attempt — no repair loop, no retry
    esc = exc.value.escalation
    for marker in ("1. Issue:", "2. Severity:", "3. Evidence:",
                   "4. Options considered:", "5. Recommendation:", "6. Expected outcome:"):
        assert marker in esc  # the PROMPT-ESC six-field package, complete


def test_rule6_gate_failure_never_retries(tmp_path):
    gate_calls = {"n": 0}

    def failing_gate(sandbox):
        gate_calls["n"] += 1
        return False, "boom"

    bridge = _bridge(tmp_path, gate=failing_gate)
    with pytest.raises(BridgeEscalation):
        bridge.run(artifact_text=GOOD_ARTIFACT, task_code="RETRY-T", title="t")
    assert gate_calls["n"] == 1  # one gate run; the bridge never retries itself
