"""Company Evolution Backlog — improvement_proposals (Phase E).

Additive, standalone table — offline suite and existing rows unaffected.

Revision ID: 0028_improvement_proposals
Revises: 0027_provider_routing_log
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.models.base import GUID

revision = "0028_improvement_proposals"
down_revision = "0027_provider_routing_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "improvement_proposals",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column("signature", sa.String(length=120), nullable=False, unique=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("technical_impact", sa.Text(), nullable=True),
        sa.Column("blueprint_ref", sa.String(length=300), nullable=True),
        sa.Column("risk", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("priority_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("roi", sa.String(length=120), nullable=True),
        sa.Column("effort", sa.String(length=120), nullable=True),
        sa.Column("recommended_solution", sa.Text(), nullable=True),
        sa.Column("alternatives", sa.Text(), nullable=True),
        sa.Column("dependencies", sa.Text(), nullable=True),
        sa.Column("debate", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_improvement_proposals_dimension", "improvement_proposals", ["dimension"])
    op.create_index("ix_improvement_proposals_priority", "improvement_proposals", ["priority"])
    op.create_index("ix_improvement_proposals_status", "improvement_proposals", ["status"])
    op.create_index("ix_improvement_proposals_created_at", "improvement_proposals", ["created_at"])


def downgrade() -> None:
    op.drop_table("improvement_proposals")
