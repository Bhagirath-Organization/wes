"""Provider routing log (Phase C).

One row per AI request the Company Brain routed to a provider: what task it was,
which provider was chosen (and the alternative / fallback), why, the estimated vs
actual latency/cost, and whether a fallback was used. Powers the Provider Learning
Engine (success/latency/cost per provider+task) and the AI Operations dashboard.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base, UUIDPrimaryKeyMixin


class ProviderRoutingLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "provider_routing_log"

    task_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False, default="route")  # route|fallback|consensus
    chosen_provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    alternative_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fallback_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    est_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    est_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
