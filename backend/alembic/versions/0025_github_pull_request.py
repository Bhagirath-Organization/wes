"""Real GitHub Pull Request tracking on pull_requests (P0 final).

Additive and fully nullable: existing rows and the offline test suite are
unaffected. Records the live GitHub PR (repo/number/url) and merge result so the
autonomous delivery pipeline (push → PR → Founder approval → merge) is auditable.

Revision ID: 0025_github_pull_request
Revises: 0024_company_memory
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0025_github_pull_request"
down_revision = "0024_company_memory"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("github_repo", sa.String(length=200)),
    ("github_number", sa.Integer()),
    ("github_url", sa.String(length=400)),
    ("merged_sha", sa.String(length=64)),
    ("merged_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column("pull_requests", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("pull_requests", name)
