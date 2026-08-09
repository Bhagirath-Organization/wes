"""SOP-library ratification tests (WES-DEC-010 step 4, second PR).

The runtime ``sop_library`` rows carried one-line legacy stubs (43–66 chars) —
the last hand-written governance text in the composed prompt after the F9
wiring. These tests pin their replacement with the ratified SOPs' operative
bodies, using the same guarantees as the Prompt Library seed (PR #9):

* **Verbatim fidelity** — each body re-derives byte-equal from its live
  ``Company/Operating-Instructions/SOP-*.md`` doc, and every seeded line exists
  verbatim in the source (provenance, independent of the extractor).
* **Idempotent upsert** — insert-missing / repair-drift in place; second run
  writes nothing.
* **Injection** — a mock-provider run's composed SOP message carries the
  ratified body, not the stub.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.seed_execution import sync_sop_library
from app.db.sop_library_content import RATIFIED_SOPS, extract_sop_body
from app.models.execution import SOP

OI_DIR = Path(__file__).resolve().parents[3] / "Company" / "Operating-Instructions"


def test_specs_shape():
    codes = [s.code for s in RATIFIED_SOPS]
    assert len(codes) == len(set(codes)) == 6
    assert {s.category.value for s in RATIFIED_SOPS} == {
        "coding", "review", "testing", "deployment", "documentation", "security",
    }
    for s in RATIFIED_SOPS:
        assert s.content.startswith("## ")
        assert len(s.content) > 1000  # a real SOP body, not a stub


@pytest.mark.skipif(not OI_DIR.exists(), reason="ratified docs tree not present (deployed runtime)")
@pytest.mark.parametrize("spec", RATIFIED_SOPS, ids=lambda s: s.code)
def test_body_matches_ratified_doc_verbatim(spec):
    raw = (OI_DIR / f"{spec.source_doc}.md").read_text(encoding="utf-8")
    assert extract_sop_body(raw) == spec.content


@pytest.mark.skipif(not OI_DIR.exists(), reason="ratified docs tree not present (deployed runtime)")
@pytest.mark.parametrize("spec", RATIFIED_SOPS, ids=lambda s: s.code)
def test_every_seeded_line_exists_in_doc(spec):
    doc_lines = set((OI_DIR / f"{spec.source_doc}.md").read_text(encoding="utf-8").splitlines())
    for line in spec.content.splitlines():
        if line:
            assert line in doc_lines, f"{spec.code}: line not verbatim: {line!r}"


def test_sync_inserts_then_idempotent(db_session):
    assert sync_sop_library(db_session) == 6
    rows = {s.code: s for s in db_session.query(SOP).all()}
    for spec in RATIFIED_SOPS:
        assert rows[spec.code].content == spec.content
        assert rows[spec.code].version == 2
    assert sync_sop_library(db_session) == 0


def test_sync_retires_legacy_stub_in_place(db_session):
    from app.domain.execution_enums import SOPCategory

    db_session.add(
        SOP(
            code="SOP-CODE",
            title="Coding SOP",
            category=SOPCategory.CODING,
            content="Write small, tested, reviewed changes. Follow the style guide.",
            version=1,
        )
    )
    db_session.commit()
    assert sync_sop_library(db_session) == 6  # 1 stub repaired + 5 inserted
    row = db_session.query(SOP).filter_by(code="SOP-CODE").one()
    assert row.version == 2
    assert row.content == next(s.content for s in RATIFIED_SOPS if s.code == "SOP-CODE")
    assert "Write small, tested, reviewed changes" not in row.content


@pytest.mark.usefixtures("orch_seeded")
def test_composed_prompt_carries_ratified_sop_body(db_session):
    """End-to-end (mock provider): the SOP message is the ratified body, not the stub."""
    import uuid as _uuid

    from app.models.ai import AIEmployee
    from app.models.orchestration import ExecutionMessage
    from app.services.orchestration import OrchestrationService

    sync_sop_library(db_session)
    ritchie = db_session.query(AIEmployee).filter_by(employee_code="AI-EMP-005").one()
    run = OrchestrationService(db_session).run_stage(ritchie.id, None, provider_name="mock")
    assert run["status"] == "completed"
    contents = [
        m.content
        for m in db_session.query(ExecutionMessage)
        .filter_by(run_id=_uuid.UUID(run["id"]))
        .all()
    ]
    sop_body = next(s.content for s in RATIFIED_SOPS if s.code == "SOP-CODE")
    assert any(sop_body in c for c in contents)
    assert not any("Write small, tested, reviewed changes. Follow the style guide." in c for c in contents)
