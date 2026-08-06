"""Pre-flight PR-1: seeding the ratified WES Prompt Library.

Covers the two guarantees that matter for this seed:

* **Verbatim fidelity** — every seeded body is byte-for-byte the operative body
  of its ratified ``Company/Operating-Instructions/*.md`` document (no
  re-summarising, no re-drafting). Proven two ways: the extraction re-derived
  from the live doc must equal the embedded constant (anti-drift), and every
  seeded line must exist verbatim in the source doc (provenance, independent of
  the extraction logic).
* **Idempotent upsert** — ``sync_prompt_library`` inserts what is missing,
  upgrades the one-line activity placeholders in place, and writes nothing on a
  second run — the ``sync_prompt_sys`` pattern generalised.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.prompt_library_content import (
    GOVERNED_PROMPTS,
    extract_prompt_body,
)
from app.db.seed_execution import sync_prompt_library
from app.domain.execution_enums import PromptType
from app.models.execution import PromptTemplate

# Repo root: tests/unit/<file> -> tests -> backend -> repo root.
OI_DIR = Path(__file__).resolve().parents[3] / "Company" / "Operating-Instructions"

EXPECTED_ACTIVITY = {
    "PROMPT-TASK": PromptType.TASK,
    "PROMPT-REVIEW": PromptType.REVIEW,
    "PROMPT-ESC": PromptType.ESCALATION,
}


def test_governed_prompts_shape():
    """13 Role Prompts + 3 activity prompts, unique codes within column limits."""
    codes = [s.code for s in GOVERNED_PROMPTS]
    assert len(codes) == len(set(codes)) == 16
    roles = [s for s in GOVERNED_PROMPTS if s.prompt_type == PromptType.ROLE]
    assert len(roles) == 13
    assert all(c.startswith("ROLE-") for c in (s.code for s in roles))
    activity = {s.code: s.prompt_type for s in GOVERNED_PROMPTS if s.code.startswith("PROMPT-")}
    assert activity == EXPECTED_ACTIVITY
    for s in GOVERNED_PROMPTS:
        assert len(s.code) <= 60 and len(s.name) <= 200  # DB column limits


@pytest.mark.skipif(not OI_DIR.exists(), reason="ratified docs tree not present (deployed runtime)")
@pytest.mark.parametrize("spec", GOVERNED_PROMPTS, ids=lambda s: s.code)
def test_seeded_body_matches_ratified_doc_verbatim(spec):
    """The embedded body equals the operative body re-derived from the live doc."""
    raw = (OI_DIR / f"{spec.code}.md").read_text(encoding="utf-8")
    assert extract_prompt_body(raw) == spec.content


@pytest.mark.skipif(not OI_DIR.exists(), reason="ratified docs tree not present (deployed runtime)")
@pytest.mark.parametrize("spec", GOVERNED_PROMPTS, ids=lambda s: s.code)
def test_every_seeded_line_exists_verbatim_in_doc(spec):
    """Provenance independent of extraction: each seeded line is a line of the doc.

    Guards the Founder's constraint directly — nothing seeded was reworded; the
    only transformation is dropping doc chrome and joining sections.
    """
    doc_lines = set((OI_DIR / f"{spec.code}.md").read_text(encoding="utf-8").splitlines())
    for line in spec.content.splitlines():
        if line == "":
            continue  # blank join line between body and Handoff footer
        assert line in doc_lines, f"{spec.code}: seeded line not found verbatim: {line!r}"


def _codes(db):
    return {p.code: p for p in db.query(PromptTemplate).all()}


def test_sync_prompt_library_inserts_then_is_idempotent(db_session):
    """First run inserts all 16; a second run writes nothing."""
    assert sync_prompt_library(db_session) == 16
    rows = _codes(db_session)
    for spec in GOVERNED_PROMPTS:
        assert rows[spec.code].content == spec.content
        assert rows[spec.code].prompt_type == spec.prompt_type
    # Idempotent: nothing to write the second time.
    assert sync_prompt_library(db_session) == 0


def test_sync_repairs_drift_in_place(db_session):
    """A drifted row is corrected without a destructive re-seed."""
    sync_prompt_library(db_session)
    row = db_session.query(PromptTemplate).filter_by(code="ROLE-BACKEND-ENGINEER").one()
    row.content = "stale"
    db_session.commit()
    assert sync_prompt_library(db_session) == 1
    fixed = db_session.query(PromptTemplate).filter_by(code="ROLE-BACKEND-ENGINEER").one()
    assert fixed.content == next(
        s.content for s in GOVERNED_PROMPTS if s.code == "ROLE-BACKEND-ENGINEER"
    )
    assert sync_prompt_library(db_session) == 0


def test_full_seed_upgrades_placeholders_and_adds_roles(exec_seeded, db_session):
    """After a full seed the activity placeholders carry verbatim bodies and the
    13 Role Prompts exist — alongside the still-current PROMPT-SYS v2."""
    rows = _codes(db_session)
    # 13 role prompts present and typed ROLE.
    role_codes = [s.code for s in GOVERNED_PROMPTS if s.prompt_type == PromptType.ROLE]
    for code in role_codes:
        assert code in rows and rows[code].prompt_type == PromptType.ROLE
    # Activity placeholders upgraded from the one-line stubs to verbatim bodies.
    for spec in GOVERNED_PROMPTS:
        if spec.code in EXPECTED_ACTIVITY:
            assert rows[spec.code].content == spec.content
            assert rows[spec.code].content.startswith("## ")  # not the stub sentence
    # The distilled Constitution is still seeded at version 2.
    assert rows["PROMPT-SYS"].prompt_type == PromptType.SYSTEM
    assert rows["PROMPT-SYS"].version == 2
