"""Project ATLAS — Repository Intelligence (business-asset) layer.

Additive tables only; existing repository engine and offline suite unaffected.

Revision ID: 0029_repository_intelligence_atlas
Revises: 0028_improvement_proposals
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision = "0029_repository_intelligence_atlas"
down_revision = "0028_improvement_proposals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repository_intelligence",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("repository_id", GUID(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_domain", sa.String(length=200), nullable=True),
        sa.Column("business_objective", sa.Text(), nullable=True),
        sa.Column("business_capability", sa.String(length=300), nullable=True),
        sa.Column("business_status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("business_value", sa.Text(), nullable=True),
        sa.Column("architecture_style", sa.String(length=120), nullable=True),
        sa.Column("maturity", sa.String(length=20), nullable=False, server_default="emerging"),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="low"),
        sa.Column("documentation_quality", sa.Float(), nullable=False, server_default="0"),
        sa.Column("knowledge_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("technical_debt", sa.Float(), nullable=False, server_default="0"),
        sa.Column("health_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("business_risk", sa.Text(), nullable=True),
        sa.Column("blueprint_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("blueprint_alignment", sa.Float(), nullable=False, server_default="0"),
        sa.Column("executive_owner", sa.String(length=120), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("owners", sa.Text(), nullable=True),
        sa.Column("modules", sa.Text(), nullable=True),
        sa.Column("reusable_capabilities", sa.Text(), nullable=True),
        sa.Column("dependencies_summary", sa.Text(), nullable=True),
        sa.Column("structured_intelligence", sa.Text(), nullable=True),
        sa.Column("blueprint_analysis", sa.Text(), nullable=True),
        sa.Column("knowledge_summary", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_intelligence_repository_id", "repository_intelligence", ["repository_id"], unique=True)
    op.create_index("ix_repository_intelligence_business_status", "repository_intelligence", ["business_status"])

    op.create_table(
        "repository_graph_nodes",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("repository_id", GUID(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("node_key", sa.String(length=300), nullable=False),
        sa.Column("node_type", sa.String(length=30), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("meta", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_graph_nodes_repository_id", "repository_graph_nodes", ["repository_id"])
    op.create_index("ix_repository_graph_nodes_node_key", "repository_graph_nodes", ["node_key"])
    op.create_index("ix_repository_graph_nodes_node_type", "repository_graph_nodes", ["node_type"])

    op.create_table(
        "repository_graph_edges",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("repository_id", GUID(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_key", sa.String(length=300), nullable=False),
        sa.Column("target_key", sa.String(length=300), nullable=False),
        sa.Column("relation", sa.String(length=40), nullable=False),
        sa.Column("meta", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_graph_edges_repository_id", "repository_graph_edges", ["repository_id"])
    op.create_index("ix_repository_graph_edges_source_key", "repository_graph_edges", ["source_key"])
    op.create_index("ix_repository_graph_edges_target_key", "repository_graph_edges", ["target_key"])

    op.create_table(
        "repository_events",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("repository_id", GUID(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("business_event", sa.String(length=300), nullable=False),
        sa.Column("business_category", sa.String(length=40), nullable=False, server_default="activity"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="system"),
        sa.Column("external_ref", sa.String(length=200), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_events_repository_id", "repository_events", ["repository_id"])
    op.create_index("ix_repository_events_event_type", "repository_events", ["event_type"])
    op.create_index("ix_repository_events_created_at", "repository_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("repository_events")
    op.drop_table("repository_graph_edges")
    op.drop_table("repository_graph_nodes")
    op.drop_table("repository_intelligence")
