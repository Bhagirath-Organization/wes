"""autonomous planning engine — milestone/sprint/task planning fields (Phase 2)

Adds the fields the Planning Engine needs to persist a company-grade plan.
Every column is nullable so existing rows and the existing API stay valid.

Revision ID: 0022_planning_engine
Revises: 0021_self_learning
"""

from alembic import op
import sqlalchemy as sa

revision = "0022_planning_engine"
down_revision = "0021_self_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Milestones: business objective, deliverables, AC, DoD, review trigger.
    op.add_column("milestones", sa.Column("business_objective", sa.Text(), nullable=True))
    op.add_column("milestones", sa.Column("deliverables", sa.Text(), nullable=True))
    op.add_column("milestones", sa.Column("acceptance_criteria", sa.Text(), nullable=True))
    op.add_column("milestones", sa.Column("definition_of_done", sa.Text(), nullable=True))
    op.add_column("milestones", sa.Column("review_trigger", sa.Text(), nullable=True))

    # Sprints: objective, capacity, exit criteria, risk level.
    op.add_column("project_sprints", sa.Column("objective", sa.Text(), nullable=True))
    op.add_column("project_sprints", sa.Column("capacity_hours", sa.Float(), nullable=True))
    op.add_column("project_sprints", sa.Column("exit_criteria", sa.Text(), nullable=True))
    op.add_column("project_sprints", sa.Column("risk_level", sa.String(20), nullable=True))

    # Work items: per-task Definition of Done.
    op.add_column("work_items", sa.Column("definition_of_done", sa.Text(), nullable=True))

    # Project: the full planning artifact (repo/gap analysis, graph, risks).
    op.add_column("projects", sa.Column("plan_artifact", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "plan_artifact")
    op.drop_column("work_items", "definition_of_done")
    op.drop_column("project_sprints", "risk_level")
    op.drop_column("project_sprints", "exit_criteria")
    op.drop_column("project_sprints", "capacity_hours")
    op.drop_column("project_sprints", "objective")
    op.drop_column("milestones", "review_trigger")
    op.drop_column("milestones", "definition_of_done")
    op.drop_column("milestones", "acceptance_criteria")
    op.drop_column("milestones", "deliverables")
    op.drop_column("milestones", "business_objective")
