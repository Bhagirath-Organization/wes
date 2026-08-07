"""Pre-flight PR-2: loading the ratified SOPs + governed docs into the Knowledge Engine.

Guarantees:

* **Verbatim fidelity** — each loaded document's content is byte-for-byte the full
  text of its ratified ``Company/Operating-Instructions/*.md`` file (no
  re-summarising, no re-drafting). Unlike the injected Prompt Library bodies, the
  whole document is the knowledge-base reference, so nothing is stripped.
* **Idempotent upsert** — ``sync_knowledge_library`` inserts what is missing,
  repairs drift in place (snapshotting a new version on content change), and writes
  nothing on a second run.
* **Retrievable** — after a full seed the 6 SOPs surface in the AI retrieval bundle
  and the governed docs are keyword-searchable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.knowledge_library_content import KNOWLEDGE_DOCS
from app.db.seed_knowledge import sync_knowledge_library
from app.domain.knowledge_enums import DocumentType, KnowledgeStatus
from app.models.knowledge import (
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeEmbeddingPlaceholder,
    KnowledgeVersion,
)
from app.services.knowledge_search import RetrievalService

OI_DIR = Path(__file__).resolve().parents[3] / "Company" / "Operating-Instructions"


def test_knowledge_docs_shape():
    """6 SOPs + 3 governed docs, unique codes within column limits."""
    codes = [d.code for d in KNOWLEDGE_DOCS]
    assert len(codes) == len(set(codes)) == 9
    sops = [d for d in KNOWLEDGE_DOCS if d.doc_type == DocumentType.SOP]
    policies = [d for d in KNOWLEDGE_DOCS if d.doc_type == DocumentType.POLICY]
    assert len(sops) == 6 and len(policies) == 3
    for d in KNOWLEDGE_DOCS:
        assert len(d.code) <= 60 and len(d.title) <= 300  # DB column limits
        assert d.summary and d.keywords  # retrieval metadata present


@pytest.mark.skipif(not OI_DIR.exists(), reason="ratified docs tree not present (deployed runtime)")
@pytest.mark.parametrize("spec", KNOWLEDGE_DOCS, ids=lambda s: s.code)
def test_content_is_verbatim_full_file(spec):
    """Loaded content equals the full ratified file, byte-for-byte."""
    assert spec.content == (OI_DIR / f"{spec.code}.md").read_text(encoding="utf-8")


def _docs(db):
    return {d.code: d for d in db.query(KnowledgeDocument).all()}


def test_sync_inserts_then_idempotent(db_session):
    """First run inserts 9 approved docs (+version +embedding placeholder); second writes nothing."""
    assert sync_knowledge_library(db_session) == 9
    docs = _docs(db_session)
    for spec in KNOWLEDGE_DOCS:
        d = docs[spec.code]
        assert d.content == spec.content
        assert d.status == KnowledgeStatus.APPROVED
        assert getattr(d.doc_type, "value", d.doc_type) == spec.doc_type.value
        # A version snapshot and an embedding placeholder exist per document.
        assert db_session.query(KnowledgeVersion).filter_by(document_id=d.id).count() >= 1
        assert db_session.query(KnowledgeEmbeddingPlaceholder).filter_by(document_id=d.id).count() == 1
    assert sync_knowledge_library(db_session) == 0


def test_sync_repairs_drift_and_snapshots_version(db_session):
    """A drifted document is corrected in place and a new version is snapshotted."""
    sync_knowledge_library(db_session)
    doc = db_session.query(KnowledgeDocument).filter_by(code="SOP-TESTING").one()
    v_before = db_session.query(KnowledgeVersion).filter_by(document_id=doc.id).count()
    doc.content = "stale"
    db_session.commit()
    assert sync_knowledge_library(db_session) == 1
    fixed = db_session.query(KnowledgeDocument).filter_by(code="SOP-TESTING").one()
    spec = next(s for s in KNOWLEDGE_DOCS if s.code == "SOP-TESTING")
    assert fixed.content == spec.content
    assert fixed.version == 2
    assert db_session.query(KnowledgeVersion).filter_by(document_id=doc.id).count() == v_before + 1
    assert sync_knowledge_library(db_session) == 0


def test_full_seed_links_categories_and_is_retrievable(knowledge_seeded, db_session):
    """After a full seed the docs are categorised, SOPs surface in retrieval, and
    governed docs are keyword-searchable."""
    docs = _docs(db_session)
    cats = {c.code: c for c in db_session.query(KnowledgeCategory).all()}
    for spec in KNOWLEDGE_DOCS:
        assert spec.code in docs
        assert docs[spec.code].category_id == cats[spec.category_code].id

    bundle = RetrievalService(db_session).retrieve_for(keywords="coverage floor", log=False)
    sop_codes = {b["code"] for b in bundle["relevant_sop"]}
    assert sop_codes & {s.code for s in KNOWLEDGE_DOCS if s.doc_type == DocumentType.SOP}

    # Governed docs are findable by keyword search (title/summary/content/keywords/code).
    hits = {d.code for d in RetrievalService(db_session).search.search("constitution")}
    assert "PROMPT-SYS" in hits
