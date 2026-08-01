"""Provider routing log for the AI Provider Orchestrator (Phase C).

Additive, standalone table — offline suite and existing rows unaffected.

Revision ID: 0027_provider_routing_log
Revises: 0026_project_plan_error
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision = "0027_provider_routing_log"
down_revision = "0026_project_plan_error"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_routing_log",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("task_type", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False, server_default="route"),
        sa.Column("chosen_provider", sa.String(length=40), nullable=False),
        sa.Column("alternative_provider", sa.String(length=40), nullable=True),
        sa.Column("fallback_provider", sa.String(length=40), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("est_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("est_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_latency_ms", sa.Integer(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_provider_routing_log_task_type", "provider_routing_log", ["task_type"])
    op.create_index("ix_provider_routing_log_chosen_provider", "provider_routing_log", ["chosen_provider"])
    op.create_index("ix_provider_routing_log_created_at", "provider_routing_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("provider_routing_log")
