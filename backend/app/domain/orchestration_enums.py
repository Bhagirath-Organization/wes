"""Enumerations for the AI Orchestration Engine (Sprint 09)."""

from enum import Enum


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ProviderHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ReviewOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    ESCALATED = "escalated"


class CollaborationType(str, Enum):
    """Kinds of structured collaboration turns (Phase 3).

    A persistent company record: every question, challenge, review, approval,
    rejection, escalation and decision is stored as a message of one of these
    types.
    """

    QUESTION = "question"
    ANSWER = "answer"
    PROPOSAL = "proposal"
    REVIEW = "review"
    APPROVAL = "approval"
    REJECTION = "rejection"
    CLARIFICATION = "clarification"
    ESCALATION = "escalation"
    DECISION = "decision"
    RESOLUTION = "resolution"
    CONCERN = "concern"
