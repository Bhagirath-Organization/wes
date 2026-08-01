"""AI workforce collaboration — structured, persistent conversations (Phase 3)

Reuses the existing conversation store (conversation_threads + execution_messages)
and extends it so a message can record WHO spoke and WHAT KIND of collaboration
turn it is (question / proposal / review / approval / rejection / escalation /
decision ...). Also links a thread to a project so collaboration is queryable per
project. Every column is nullable → existing rows and writers stay valid.

Revision ID: 0023_workforce_collaboration
Revises: 0022_planning_engine
"""

from alembic import op
import sqlalchemy as sa

revision = "0023_workforce_collaboration"
down_revision = "0022_planning_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversation_threads", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.add_column("conversation_threads", sa.Column("kind", sa.String(40), nullable=True))
    op.create_index(
        "ix_conversation_threads_project_id", "conversation_threads", ["project_id"]
    )
    op.add_column("execution_messages", sa.Column("speaker_employee_id", sa.Uuid(), nullable=True))
    op.add_column("execution_messages", sa.Column("to_employee_id", sa.Uuid(), nullable=True))
    op.add_column("execution_messages", sa.Column("message_type", sa.String(30), nullable=True))
    op.add_column("execution_messages", sa.Column("speaker_role", sa.String(60), nullable=True))


def downgrade() -> None:
    op.drop_column("execution_messages", "speaker_role")
    op.drop_column("execution_messages", "message_type")
    op.drop_column("execution_messages", "to_employee_id")
    op.drop_column("execution_messages", "speaker_employee_id")
    op.drop_index("ix_conversation_threads_project_id", table_name="conversation_threads")
    op.drop_column("conversation_threads", "kind")
    op.drop_column("conversation_threads", "project_id")
