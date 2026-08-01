"""Improvement proposal / Company Evolution Backlog (Phase E).

Each row is a self-discovered improvement opportunity: the weakness, its real
evidence, the executive board's debate, the recommended solution and the business
framing the Founder decides on. Ranked by business value, not engineering effort.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ImprovementProposal(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "improvement_proposals"

    dimension: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)  # dedupe key
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    blueprint_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium", index=True)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    roi: Mapped[str | None] = mapped_column(String(120), nullable=True)
    effort: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recommended_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternatives: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON list
    dependencies: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON list
    debate: Mapped[str | None] = mapped_column(Text, nullable=True)           # JSON: executive opinions
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
