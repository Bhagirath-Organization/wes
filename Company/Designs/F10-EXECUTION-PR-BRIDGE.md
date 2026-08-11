# F10 — Execution→PR Bridge: Design for Founder Decision

| Field | Detail |
|-------|--------|
| **Document** | F10 bridge design (engineering design doc — not a governed OI document) |
| **Status** | DRAFT — awaiting Founder decisions A1/A2/A3; scoped PRs follow the decisions |
| **Evidence base** | Mission finding F10 (orchestration output ends at text); mission card trace (2026-08-08 snapshot); dev-engine survey (full-system audit 2026-08-07) |
| **Rails** | Every implementation PR: SOP-CODING end-to-end, Founder merge. Budget: envelope-governed (WES-DEC-011). Production releases per SOP-DEPLOYMENT, Founder-gated. |

---

## §A — Context: the gap, precisely

The live mission proved (F10) that the governed execution path ends at **reviewed text**: an AI
employee's approved output never becomes a commit, a branch, or a PR. The real `truncate()`
shipped only because a human (the agent, Founder-merged) carried the artifacts into PR #13 by
hand. Meanwhile a **Development Engine already exists** (`development_service.py` →
`dev_generation.py` [real LLM file-content since Sprint 24] → `dev_modification.py` [safe writes]
→ `dev_git.py` [branch/PR via the GitHub App, key mounted in green]) — 🟡 never verified
end-to-end; its 135 historical tasks are July-era experiments (100 failed, ollama-era).

**Consequence visible on the Founder's screen today** (post-deploy snapshot): the mission card
shows "Review / 70% / Needs your approval" because the mission's `development_tasks` mirrors sit
`pr_ready` forever — work that ships through the human lane never advances the machine lifecycle.

## §B — The bridge flow (end-to-end, lifecycle-truth included)

```
plan approved (+envelope, one act)                                 [exists ✓]
  → task execution: governed run produces the reviewed artifact    [exists ✓]
  → review verdict: approved                                       [exists ✓]
  ─────────────────────── THE BRIDGE (new) ───────────────────────
  → B1  parse the approved artifact into concrete file changes
        (file blocks; reject-and-return if the artifact has none)
  → B2  apply to a fresh feature branch (never main; SOP-CODING §6)
  → B3  verification gate (per A3): tests + coverage floor in an
        isolated runner; a failing gate STOPS the bridge — task
        returns to Engineering with the evidence, honestly
  → B4  open the PR (authority per A2) with provenance: run ids,
        artifact hash, verdicts, costs — the PR-body discipline
        the phase already practices
  → B5  FOUNDER MERGE — unchanged, non-negotiable (PROMPT-SYS §6)
  ────────────────── LIFECYCLE TRUTH (part of the bridge) ─────────
  → B6  on merge success, the bridge ADVANCES THE RECORD:
        • development_tasks: pr_ready → merged (→ deployed when a
          release later carries it)
        • the mission's work_items → done
        • projects.status advances past 'planning'
        so FounderMissionControl derives "Deployment/Completed" and
        the mission card TELLS THE TRUTH. This is IN-SCOPE of F10 —
        not a separate cosmetic fix (Founder direction, 2026-08-08).
        Includes a one-time reconciliation of the 5 existing
        TEST-MISSION-01 mirrors (their work merged as PR #13).
```

Failure honesty at every step: a bridge that cannot parse, apply, or verify **stops and reports
with evidence** — a failed bridge run is a valid outcome, never silently retried (charter ethos).

## §C — Founder decisions

**DECIDED (Founder, 2026-08-08): A1-a · A2-a · A3-a — all three recommendations approved.**
The option tables remain for the record; **A4 was identified as missing and ruled by the Founder
in the same review** (below).

### A1 — Which lane drives the bridge?
| Option | Description | Trade-off |
|---|---|---|
| **A1-a (recommended)** | **Thin artifact-to-PR lane**: take the APPROVED orchestration artifact (already governed + reviewed) → B1–B6 directly; reuse `dev_git` for branch/PR mechanics only | Minimal new machinery; trusts the governed review lane we've proven; dev-engine's unverified planner/generator stays out of the critical path |
| A1-b | **Extend the Development Engine**: route approved tasks into `development_service`'s full pipeline (its own plan→generate→modify→test→PR) | Reuses more existing code but puts a 🟡 unverified engine (July: 100/130 failed) in the middle; its generator would *re-create* content the governed run already produced |
| A1-c | Staged: A1-a now, evaluate A1-b as a later upgrade with its own verification mission | Slowest total path; cleanest risk isolation |

### A2 — PR-opening authority
| Option | Description | Trade-off |
|---|---|---|
| **A2-a (recommended)** | Bridge auto-opens the PR when review verdict = approved; **merge stays Founder-only** | Matches WES-DEC-002's existing pattern (App-token PRs, Founder merges); zero new authority — the PR is just a prepared decision |
| A2-b | Founder click required even to open the PR | Extra gate, extra friction; the PR itself is inert without a merge |
| A2-c | Auto-PR + auto-assign reviewers + auto-rerun on comments | Furthest autonomy; premature before one verified bridge cycle |

### A3 — Verification gate before the PR opens
| Option | Description | Trade-off |
|---|---|---|
| **A3-a (recommended)** | **Full suite + coverage floor** in an isolated container (the proven pattern from this phase) + the artifact's own tests must be present and pass | Strongest honest gate; ~2-4 min per bridge run |
| A3-b | Targeted tests only (changed-path) | Faster, weaker; regression risk rides to the PR |
| A3-c | QA-employee verdict run replaces automated gate | Governance-pure but puts an LLM verdict where a deterministic gate belongs |

### A4 — Commit attribution (Founder ruling, 2026-08-08)
**Ruled with the design review** (was missing from the draft): every bridge-authored commit
carries the human-vs-AI distinction **permanently in git history**, plus machine-parseable
provenance:

- **Author** = the AI employee who produced the approved artifact, in the form
  `<Name> (WES <Role>) <bots+wes-<employee>@…>` (mailbox pattern design-level; exact domain set
  at implementation from configuration, never hard-coded).
- **Committer** = the App-token identity (the mechanical actor), unchanged from WES-DEC-002
  practice.
- **Trailers** (machine-parseable, always both):
  `WES-Run: <run_id>` and `WES-Mission: <mission_id>`.

**git-log preview (the exact shape the bridge writes):**

```
commit 3f9c2ab7…
Author: Ritchie (WES Backend Engineer) <bots+wes-ritchie@wes.studio>
Commit: wes-oi-app[bot] <wes-oi-app[bot]@users.noreply.github.com>

    feat(core): is_blank() text predicate (bridge, TEST-MISSION-01)

    <body per SOP-CODING: what/why, acceptance criteria mapping,
    verification summary — the discipline every phase PR already carries>

    WES-Run: 7aa4d3a7-eb1f-4371-8ac0-d77bdfd7d8c6
    WES-Mission: f61b198c-e30e-4540-bb82-0a90221f9551
```

One glance at `git log` answers "human or AI?" forever; one `git log --format=%(trailers)` feeds
any future provenance tooling. PR-1 implements this format; a test pins author/committer split
and both trailers.

## §C-2 — Sandbox hard rules (explicit, Founder-confirmed 2026-08-08)
The bridge operates ONLY in an isolated checkout it creates and owns. Non-negotiable, testable:

1. **Never the live working tree** — the bridge never reads from or writes to `/opt/wes-green`'s
   working tree; it clones/checks out into its own sandbox path per run.
2. **Never ATLAS files** — the standing ruling holds mechanically: the bridge's apply step
   REFUSES any artifact touching ATLAS paths (`app/api/v1/{planning,engineering}.py`,
   `app/services/{execution_planning,engineering_execution}.py`, `app/models/{planning,
   engineering}.py`, `alembic/versions/003{0,1}_*atlas*`, `.s*.txt`) — refusal, not skip.
3. **Never force-push** (PROMPT-SYS §9) — mechanically absent: the bridge has no force flag.
4. **Never push to `main`** (PROMPT-SYS §9) — the bridge pushes only `feature/bridge/*` branches;
   a guard asserts the ref before any push.
5. **Sandbox failure = preserve-as-evidence** — a failed apply/gate leaves the sandbox intact
   (read-only), records its path + state in the failure report, and never auto-cleans until the
   Founder-visible report is filed.
6. **v1 has NO LLM-repair loop** — if the approved artifact does not apply cleanly (parse
   failure, conflict, missing file blocks, gate failure), the bridge STOPS and raises a
   **PROMPT-ESC escalation** (six-field package) with the evidence. It never asks a model to
   "fix" the artifact, never guesses intent. Repair loops, if ever wanted, are a separate
   Founder decision with their own design.

Each rule ships with a test in PR-1 (refusal paths are asserted, not assumed).

## §D — Scoped-PR rollout (decisions taken: A1-a / A2-a / A3-a / A4)
1. **F10-PR-1 — bridge core** (B1–B4 per decisions): parser, branch/apply, gate, PR-open; unit +
   mock-provider integration tests; no lifecycle writes yet.
2. **F10-PR-2 — lifecycle truth** (B6): merge-success advancement (tasks/work-items/project) +
   the one-time TEST-MISSION-01 mirror reconciliation + mission-card regression evidence
   (the card must read "Deployment/Completed" from real rows).
3. **F10-PR-3 — verified live cycle**: one real end-to-end bridge mission (small utility class,
   envelope-governed) — the bridge's own "run #2": PASS only when a machine-opened PR carrying a
   verified change lands behind a Founder merge and the card tells the truth. 5-part evidence
   report.

## §E — Rails
Envelope governs all bridge-era spend (WES-DEC-011); ATLAS working tree untouched; production
releases only per SOP-DEPLOYMENT; every gate failure = STOP + evidence; SQLite/Postgres-parity
lesson (F15) applies to any new value shapes.

## §F — Out of scope here; formally scoped elsewhere (Founder direction, 2026-08-08)
The **seed_ai reconciliation package** (queued after F11) formally gains two items from the
post-deploy snapshot, in addition to its existing four (CEO/CTO role mapping, Turing→canonical
renames, Learning Center refresh, orphan-tasks trace):
5. **Demo-data archiving / era-tagging** — July-era projects/tasks/proposals archived or
   era-stamped so the decision queue, mission list, and aggregate tiles read governed reality
   (the "40 decisions ≈ 0 real" fix).
6. **Envelope UI affordance** — the `approved_budget` field on the ProjectPlan approve action
   (API accepts it today; the glass cannot send it).
Scope note only — work executes at its turn in the queue.
