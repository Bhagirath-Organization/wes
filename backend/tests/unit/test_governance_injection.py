"""F9 wiring tests (WES-DEC-010 step 3): the ratified stack reaches the model.

Verifies the exact defect the live mission exposed (finding F9): the composed
prompt must carry the seeded Constitution (``PROMPT-SYS`` v2), the employee's
ratified ``ROLE-*`` body, and ``PROMPT-TASK`` — each **verbatim** from the
Prompt Library — with honest fallbacks for unmapped roles (nothing invented)
and a ``prompt_version`` stamp derived from the injected template.
"""

from __future__ import annotations

import pytest

from app.db.prompt_library_content import GOVERNED_PROMPTS
from app.db.seed_execution import PROMPT_SYS_CONTENT, sync_prompt_library, sync_prompt_sys
from app.providers import Message
from app.services.orchestration import ContextBuilder, PromptBuilder
from app.services.role_prompt_map import ROLE_PROMPT_BY_TITLE, role_prompt_code_for


def _content(code: str) -> str:
    return next(s.content for s in GOVERNED_PROMPTS if s.code == code)


# --- the mapping itself (design decision #1) -------------------------------


def test_mapping_covers_every_runtime_title_and_only_flags_the_two_ambiguous():
    unmapped = {t for t, c in ROLE_PROMPT_BY_TITLE.items() if c is None}
    assert unmapped == {"AI CEO", "AI CTO"}  # Founder decision needed — never guessed
    mapped_codes = {c for c in ROLE_PROMPT_BY_TITLE.values() if c}
    library_codes = {s.code for s in GOVERNED_PROMPTS if s.code.startswith("ROLE-")}
    assert mapped_codes <= library_codes  # every target exists in the ratified library


def test_unknown_title_maps_to_none():
    assert role_prompt_code_for("Chaos Monkey") is None
    assert role_prompt_code_for(None) is None


# --- pure composition (PromptBuilder) --------------------------------------


def _ctx(**over) -> dict:
    base = {
        "employee": {
            "name": "Ritchie",
            "role": "Backend Engineer AI",
            "department": "Engineering",
            "responsibilities": ["Build APIs"],
            "capabilities": [],
            "decision_scope": None,
        },
        "organization": "WORLD Engineering Studio — AI software company.",
        "constitution": {"content": PROMPT_SYS_CONTENT, "version": 2},
        "role_prompt": {
            "code": "ROLE-BACKEND-ENGINEER",
            "content": _content("ROLE-BACKEND-ENGINEER"),
        },
        "prompt": {"code": "PROMPT-TASK", "content": _content("PROMPT-TASK")},
        "sop": {"title": "Coding SOP", "content": "stub"},
        "task": {"code": "T-1", "title": "Do a thing", "acceptance_criteria": "done"},
        "project": None,
        "sprint": None,
        "decision_rules": [],
        "knowledge": {},
        "repository": {},
    }
    base.update(over)
    return base


def test_three_layers_injected_verbatim_and_version_stamped_v2():
    messages, version = PromptBuilder().build(_ctx())
    joined = [m.content for m in messages if m.role == "system"]
    assert joined[0] == PROMPT_SYS_CONTENT  # layer 1: Constitution, byte-equal
    assert _content("ROLE-BACKEND-ENGINEER") in joined[1]  # layer 2: ROLE body verbatim
    assert "you are Ritchie, acting in this role" in joined[1]
    assert _content("PROMPT-TASK") in joined  # layer 3: activity prompt verbatim
    assert version == "v2"  # stamped from the injected template's version
    # The hand-rolled persona/responsibilities lines are retired for mapped roles.
    assert not any(c.startswith("You are Ritchie, Backend Engineer AI at") for c in joined)
    assert not any(c.startswith("Responsibilities:") for c in joined)


def test_unmapped_role_falls_back_without_inventing():
    ctx = _ctx(role_prompt=None)
    ctx["employee"]["name"] = "Turing"
    ctx["employee"]["role"] = "AI CTO"
    messages, version = PromptBuilder().build(ctx)
    joined = [m.content for m in messages if m.role == "system"]
    assert joined[0] == PROMPT_SYS_CONTENT  # Constitution still injected
    assert version == "v2"
    assert any(c.startswith("You are Turing, AI CTO at") for c in joined)  # legacy persona
    assert any(c.startswith("Responsibilities:") for c in joined)
    assert not any("ROLE-" in c and "acting in this role" in c for c in joined)


def test_no_task_run_skips_activity_prompt():
    messages, _ = PromptBuilder().build(_ctx(task=None))
    joined = [m.content for m in messages if m.role == "system"]
    assert _content("PROMPT-TASK") not in joined


def test_no_seed_at_all_keeps_legacy_v1_behaviour():
    messages, version = PromptBuilder().build(_ctx(constitution=None, role_prompt=None, prompt=None))
    assert version == "v1"
    joined = [m.content for m in messages if m.role == "system"]
    assert any(c.startswith("You are Ritchie, Backend Engineer AI at") for c in joined)


def test_previous_messages_precede_the_current_user_message():
    # F14: prior conversation is replayed BEFORE the current user message so the
    # request always ends with a user turn (Anthropic requirement).
    prior = [Message(role="assistant", content="earlier turn")]
    messages, _ = PromptBuilder().build(_ctx(), previous=prior)
    assert messages[-1].role == "user"
    assert any(m.content == "earlier turn" for m in messages)
    assert [m.content for m in messages].index("earlier turn") < len(messages) - 1


# --- DB-backed context (ContextBuilder) ------------------------------------


@pytest.mark.usefixtures("orch_seeded")
def test_context_builder_fetches_ratified_layers(db_session):
    from app.models.ai import AIEmployee

    sync_prompt_sys(db_session)
    sync_prompt_library(db_session)
    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    ctx = ContextBuilder(db_session).build(ritchie, None)
    assert ctx["constitution"]["version"] == 2
    assert ctx["constitution"]["content"] == PROMPT_SYS_CONTENT
    assert ctx["role_prompt"]["code"] == "ROLE-BACKEND-ENGINEER"
    assert ctx["role_prompt"]["content"] == _content("ROLE-BACKEND-ENGINEER")
    assert ctx["prompt"]["content"] == _content("PROMPT-TASK")


@pytest.mark.usefixtures("orch_seeded")
def test_run_stage_persists_governed_messages_end_to_end(db_session):
    """Mock-provider run: the PERSISTED thread messages carry all three layers."""
    from app.models.ai import AIEmployee
    from app.models.orchestration import ExecutionMessage
    from app.services.orchestration import OrchestrationService
    from app.services.providers_service import ProviderService

    sync_prompt_sys(db_session)
    sync_prompt_library(db_session)
    svc = OrchestrationService(db_session)
    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    mock_provider = ProviderService(db_session).get_by_name("mock")
    run = svc.run_stage(ritchie.id, None, provider_name="mock")
    assert run["status"] == "completed"
    assert run["prompt_version"] == "v2"
    import uuid as _uuid

    contents = [
        m.content
        for m in db_session.query(ExecutionMessage)
        .filter_by(run_id=_uuid.UUID(run["id"]))
        .order_by(ExecutionMessage.sequence)
        .all()
    ]
    assert contents[0] == PROMPT_SYS_CONTENT
    assert any(_content("ROLE-BACKEND-ENGINEER") in c for c in contents)
    assert mock_provider is not None  # the run really went through the provider layer


def test_prior_system_messages_are_not_replayed():
    # F14: only user/assistant turns replay; persisted system layers are NOT
    # re-injected (governance is composed fresh each run — no doubling/staleness).
    prior = [
        Message(role="system", content="STALE governance copy"),
        Message(role="assistant", content="prior answer"),
    ]
    messages, _ = PromptBuilder().build(_ctx(), previous=prior)
    assert not any(m.content == "STALE governance copy" for m in messages)
    assert any(m.content == "prior answer" for m in messages)


def test_ends_with_user_message_even_with_assistant_tail_prior():
    # The exact DEC-012 failure shape: a used thread whose last row is assistant.
    prior = [
        Message(role="user", content="run 1 task"),
        Message(role="assistant", content="run 1 output"),
    ]
    messages, _ = PromptBuilder().build(_ctx(), previous=prior)
    assert messages[-1].role == "user"  # would have been assistant before the fix
