"""Project ATLAS — Repository Intelligence (business-asset) ORM models.

A business-intelligence layer on top of the existing (Sprint 12) technical
repository engine. Where `repository.py` models source code, these models model
each repository as a *business asset*: its domain, objective, executive owners,
health, blueprint alignment, the structured knowledge graph, and a store of
business-translated events.

Read-only with respect to the repositories themselves; ATLAS never modifies,
pushes, branches, merges or deletes. It only understands.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class RepositoryIntelligence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The company's business understanding of one repository."""

    __tablename__ = "repository_intelligence"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    # Business understanding
    business_domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_capability: Mapped[str | None] = mapped_column(String(300), nullable=True)
    business_status: Mapped[str] = mapped_column(String(20), nullable=False, default="new", index=True)
    business_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Architecture & health
    architecture_style: Mapped[str | None] = mapped_column(String(120), nullable=True)
    maturity: Mapped[str] = mapped_column(String(20), nullable=False, default="emerging")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    documentation_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    knowledge_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    technical_debt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    business_risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Blueprint alignment
    blueprint_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    blueprint_alignment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Ownership & confidence
    executive_owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Structured intelligence (JSON blobs — never surfaced verbatim to the Founder)
    owners: Mapped[str | None] = mapped_column(Text, nullable=True)                  # JSON
    modules: Mapped[str | None] = mapped_column(Text, nullable=True)                 # JSON
    reusable_capabilities: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    dependencies_summary: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON
    structured_intelligence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    blueprint_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON
    knowledge_summary: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RepositoryGraphNode(UUIDPrimaryKeyMixin, Base):
    """A node in the structured repository graph.

    Repositories -> Projects -> Modules -> Capabilities -> Knowledge ->
    Blueprint -> Executives -> Dependencies.
    """

    __tablename__ = "repository_graph_nodes"

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    node_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RepositoryGraphEdge(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "repository_graph_edges"

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    target_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    relation: Mapped[str] = mapped_column(String(40), nullable=False)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RepositoryEvent(UUIDPrimaryKeyMixin, Base):
    """An ingested engineering event, translated into a company (business) event.

    The engineering-domain `event_type` and `external_ref` are stored for the
    company's own understanding; only `business_event` / `business_category`
    are ever surfaced to the Founder.
    """

    __tablename__ = "repository_events"

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    business_event: Mapped[str] = mapped_column(String(300), nullable=False)
    business_category: Mapped[str] = mapped_column(String(40), nullable=False, default="activity")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="system")
    external_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
