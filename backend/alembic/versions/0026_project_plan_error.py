"""Add projects.plan_error for async planning failure visibility.

Additive, nullable — offline suite and existing rows unaffected.

Revision ID: 0026_project_plan_error
Revises: 0025_github_pull_request
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0026_project_plan_error"
down_revision = "0025_github_pull_request"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("plan_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "plan_error")
