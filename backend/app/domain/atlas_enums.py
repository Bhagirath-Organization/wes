"""Enumerations for Project ATLAS — Repository Intelligence Engine (Sprint 01).

Business-asset layer over the existing (Sprint 12) technical repository engine.
"""

from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class RepositoryMaturity(str, Enum):
    EMERGING = "emerging"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    MATURE = "mature"


class BusinessStatus(str, Enum):
    """The Founder-facing state of a repository as a business asset."""

    NEW = "new"                 # connected, not yet understood
    UNDERSTOOD = "understood"   # analysed, intelligence captured
    ACTIVE = "active"           # actively delivering business value
    STABLE = "stable"           # mature, low-change asset
    LEGACY = "legacy"           # older asset, candidate for evolution


class GraphNodeType(str, Enum):
    REPOSITORY = "repository"
    PROJECT = "project"
    MODULE = "module"
    CAPABILITY = "capability"
    KNOWLEDGE = "knowledge"
    BLUEPRINT = "blueprint"
    EXECUTIVE = "executive"
    DEPENDENCY = "dependency"


class GraphRelation(str, Enum):
    DELIVERS = "delivers"          # repository -> project
    CONTAINS = "contains"          # repository -> module
    PROVIDES = "provides"          # module -> capability
    DOCUMENTS = "documents"        # repository -> knowledge
    ALIGNS_WITH = "aligns_with"    # repository -> blueprint
    OWNED_BY = "owned_by"          # repository -> executive
    DEPENDS_ON = "depends_on"      # repository -> dependency


class RepositoryEventType(str, Enum):
    """Engineering-domain event kinds ingested from the platform."""

    REPOSITORY_CREATED = "repository_created"
    REPOSITORY_ANALYSED = "repository_analysed"
    BRANCH_CREATED = "branch_created"
    PULL_REQUEST = "pull_request"
    MERGE = "merge"
    RELEASE = "release"
    TAG = "tag"
    ISSUE = "issue"
    DISCUSSION = "discussion"
    ACTION = "action"
