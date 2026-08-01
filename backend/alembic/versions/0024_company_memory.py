"""company memory, knowledge graph & semantic learning (Phase 4)

Extends the existing AgentMemory store with the metadata the Company Memory
System requires (importance, confidence, category, author role, and a real
embedding vector) and adds a lightweight memory-to-memory link table for the
knowledge graph. All additive / nullable → backward compatible.

Revision ID: 0024_company_memory
Revises: 0023_workforce_collaboration
"""

from alembic import op
import sqlalchemy as sa

revision = "0024_company_memory"
down_revision = "0023_workforce_collaboration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_memories", sa.Column("category", sa.String(60), nullable=True))
    op.add_column("agent_memories", sa.Column("importance", sa.Float(), nullable=True))
    op.add_column("agent_memories", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("agent_memories", sa.Column("author_role", sa.String(60), nullable=True))
    op.add_column("agent_memories", sa.Column("embedding", sa.Text(), nullable=True))
    op.add_column("agent_memories", sa.Column("embedding_model", sa.String(60), nullable=True))
    op.create_index("ix_agent_memories_category", "agent_memories", ["category"])

    op.create_table(
        "memory_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_memory_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("target_memory_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("relation", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("memory_links")
    op.drop_index("ix_agent_memories_category", table_name="agent_memories")
    op.drop_column("agent_memories", "embedding_model")
    op.drop_column("agent_memories", "embedding")
    op.drop_column("agent_memories", "author_role")
    op.drop_column("agent_memories", "confidence")
    op.drop_column("agent_memories", "importance")
    op.drop_column("agent_memories", "category")
