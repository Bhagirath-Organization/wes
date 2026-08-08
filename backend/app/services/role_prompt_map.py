"""Runtime AI-role → ratified Role-Prompt mapping (F9 wiring; WES-DEC-010 step 3).

Minimum-viable mapping ONLY: exactly what governance injection needs to pick the
right ratified ``ROLE-*`` template (``prompt_templates``, seeded verbatim by
PR #9) for the AI employees that exist at runtime today (``seed_ai.py`` titles,
confirmed live in the green DB). It is **not** the seed_ai ↔ canonical-org
reconciliation — that remains an open Founder decision (INVENTORY §6.5 item).

Unmapped titles return ``None`` and the composer falls back to the legacy
persona line — nothing is invented (PROMPT-SYS: "Not defined — never invent").

FOUNDER DECISION NEEDED (deliberately unmapped — do not guess):
* ``AI CEO`` — the closest canonical analog would be ``ROLE-STUDIO-DIRECTOR``
  (both are "the highest AI role"), but asserting that equivalence IS the
  seed_ai divergence question itself.
* ``AI CTO`` — the canonical 13-role org has no CTO; ``ROLE-SOFTWARE-ARCHITECT``
  already belongs to the Chief Software Architect.
"""

from __future__ import annotations

# Runtime ai_roles.title (seed_ai) -> ratified PromptTemplate.code (ROLE type).
ROLE_PROMPT_BY_TITLE: dict[str, str | None] = {
    "AI CEO": None,  # FOUNDER DECISION NEEDED (see module docstring)
    "AI CTO": None,  # FOUNDER DECISION NEEDED (see module docstring)
    "Chief Software Architect": "ROLE-SOFTWARE-ARCHITECT",
    "AI Product Manager": "ROLE-PRODUCT-MANAGER",
    "Backend Engineer AI": "ROLE-BACKEND-ENGINEER",
    "Frontend Engineer AI": "ROLE-FRONTEND-ENGINEER",
    "AI Engineer": "ROLE-AI-ENGINEER",
    "QA Engineer AI": "ROLE-QA-ENGINEER",
    "Security Engineer AI": "ROLE-SECURITY-ENGINEER",
    "DevOps Engineer AI": "ROLE-DEVOPS-AUTOMATION-ENGINEER",
    "UI/UX Designer AI": "ROLE-UX-UI-DESIGNER",
    "Technical Writer AI": "ROLE-TECHNICAL-WRITER",
}


def role_prompt_code_for(role_title: str | None) -> str | None:
    """Return the ratified ROLE-* template code for a runtime role title.

    ``None`` means no safe mapping exists (unknown title, or a title whose
    mapping awaits a Founder decision) — the caller must fall back without
    inventing authority.
    """
    if not role_title:
        return None
    return ROLE_PROMPT_BY_TITLE.get(role_title)
