# WES-DEC-002 — Agent authority: create Pull Requests and execute Founder-instructed merges via the GitHub App

| Field | Detail |
|-------|--------|
| **Decision ID** | WES-DEC-002 |
| **Date** | 2026-08-04 |
| **Owner** | Founder / Owner (Human) |
| **Status** | Approved |

## Decision Summary
An AI agent operating on WES repositories **may create Pull Requests** and **may execute a merge
that the Founder has explicitly instructed**, using a short-lived **GitHub App installation
token**. The **decision to merge remains Founder-only**; the agent executes it, it never decides it.

## Reason
- The available personal access token cannot create PRs (lacks pull-request write) and is
  blocked by an organization token-lifetime policy; the WES GitHub App is the sanctioned path.
- Using the App private key is a sensitive action; it must be gated by explicit Founder
  authorization and never used to *decide* a merge.
- This preserves the Constitution's Founder-only merge gate (PROMPT-SYS §6) while allowing the
  agent to perform the mechanical create/merge steps once the Founder has approved.

## Alternatives Considered
- **Agent merges autonomously when tests pass.** Rejected — violates the Founder-only merge gate
  (Constitution §6; Blueprint Vol 04/05).
- **Founder performs every merge manually in GitHub.** Rejected — unnecessary friction; the
  decision is what must stay with the Founder, not the button-press.
- **Grant the agent a long-lived PAT with write scope.** Rejected — org policy forbids it and a
  standing broad token is a security risk; short-lived App installation tokens are preferred.

## Final Decision
The agent is authorized to: (a) push branches; (b) open Pull Requests via the GitHub App; and
(c) execute a merge **only when the Founder has explicitly instructed that specific merge**. The
agent must **never** initiate a merge on its own judgement, never force-push, never delete
branches/repositories, and never bypass review — consistent with PROMPT-SYS §6 and §9.

## Impact
- Mechanism: mint an RS256-signed installation token from the WES GitHub App
  (`WES_GITHUB_APP_*`, key at `/opt/wes-ops/secrets/gh_app_key.pem`); private key never leaves
  the host and is never printed.
- Each Founder-instructed merge is recorded (PR number + merge SHA) in the `INVENTORY` / relevant
  work record. First application: PR #1 (`9945792`), merged on Founder instruction 2026-08-04.

## References
- `Company/Operating-Instructions/PROMPT-SYS.md` §6 (Founder-only gates), §9 (safety)
- Related: [[WES-DEC-001]]
