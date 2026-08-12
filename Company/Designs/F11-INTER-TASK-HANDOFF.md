# F11 — Inter-Task Artifact Handoff (Design Charter)

| Field | Detail |
|---|---|
| **Finding** | F11 — "No inter-task artifact handoff (T004 proved it; fresh thread per task, `prior=[]`)." |
| **Status** | **DESIGN — awaiting Founder decisions.** No code until D1–D5 are decided. |
| **Treatment** | F10-charter style: state the real current wiring, then present options + explicit Founder-decision points. |
| **Governance** | Every resulting PR = SOP-CODING end-to-end, coverage floor ≥ 71% (WES-DEC-004), Founder-only merges (WES-DEC-002). ATLAS files never touched. Prefer **no schema change** (the needed tables already exist). |

---

## 1. The problem, precisely (grounded in the live code + DB)

When a mission is decomposed into work items, each becomes a `DevelopmentTask` and runs through `DevelopmentService.run_workflow()` **independently**. Today a task's context is built from:

- **Semantic long-term memory** — `MemoryService.recall(...)` (WP8, `development_service.py:149`) returns *summaries* of prior implementations.
- **Learned rules** — `LearningService.apply(...)` (WP9, `:161`).
- **Repository/architecture intelligence** — repo modules/symbols.

It is **not** built from its predecessor tasks' **actual outputs**. Concretely, three facts are all true today:

1. **The DAG already exists but is not used for handoff.** `work_dependencies` (18 rows: `work_item_id → depends_on_id, type`) models task dependencies — but `run_workflow` does not read it to pull a predecessor's work.
2. **Every prior task's real artifacts are already persisted but never re-injected.** `generated_changes` (`task_id, path, content, diff, rationale`) holds each task's exact files/diffs; a successor task never receives them.
3. **Each task runs in a fresh sandbox off `main`** (`dev_git` creates a new per-task workspace), so a successor does not physically build on a predecessor's branch.

**"Handoff" today is intra-task only.** `development_handoffs` (371 rows) records role→role handoffs *within a single task* (`_record_handoffs(task)`, `:492` — `from_employee_id/to_employee_id`, `from_role/to_role`, `stage`, `summary`), keyed on `task_id`. There is **no** task→task artifact channel.

**Consequence (observed):** in TEST-MISSION-01, T004 depended on earlier tasks yet executed with `prior=[]` — it could not see what T001–T003 produced, so it re-derived or guessed context. This is a direct contributor to the [system audit](../../../../tmp/WES-SYSTEM-AUDIT.md)'s 74% task-failure finding: a task that should build on a predecessor instead starts blind.

**Non-goal for F11:** fixing the model/codegen quality itself. F11's job is to make sure a task *sees the right upstream context and code*; raising raw generation quality is a separate track.

---

## 2. Design dimensions → the five Founder decisions

Each decision is independent; my recommendation is marked **▶**. Trade-offs are stated so the Founder can overrule any of them.

### D1 — Workspace model (do tasks physically build on each other?)
| Option | What it means | Trade-off |
|---|---|---|
| **D1-a** Fresh sandbox per task off `main` (today) | Full isolation; zero build-on | Successor never sees predecessor code; simplest; current behavior |
| **D1-b** Successor branches off predecessor's branch (chained) | Real build-on; predecessor's uncommitted code is present | Ordering + rebase complexity; a failed predecessor poisons the chain |
| **▶ D1-c** Shared **mission workspace**, tasks run **sequentially** in dependency order | One sandbox per mission; each task commits, next task starts from that tree | True build-on with the least git gymnastics; serializes the mission (slower); needs conflict handling |

*Why ▶ D1-c:* it is the smallest change that actually delivers "the next task sees the last task's code," and it composes cleanly with D3 (ordering). D1-b is more parallel but the 74% failure rate makes chained branches fragile.

### D2 — Handoff artifact granularity (what the successor receives)
| Option | Payload | Trade-off |
|---|---|---|
| **D2-a** Summary only (today) | memory summaries | cheap tokens, lossy, already insufficient |
| **▶ D2-b** Structured **artifact manifest** | per predecessor: files created/modified (`generated_changes.path`), key new symbols, public API, branch/PR ref, one-line rationale | high signal / bounded tokens; needs a small manifest builder (no schema change — reads `generated_changes`) |
| **D2-c** Full diffs | predecessor `generated_changes.diff` verbatim | highest fidelity; large token cost; risks blowing the mission budget envelope (WES-DEC-011) |

*Why ▶ D2-b:* the model needs to know **what exists and where**, not re-read every line. D2-c can be an opt-in for small missions.

### D3 — Ordering authority (is the DAG enforced?)
| Option | Behavior | Trade-off |
|---|---|---|
| **D3-a** Independent execution (today) | tasks enqueue in any order | fast, but dependents run before dependencies |
| **▶ D3-b** Topological ordering from `work_dependencies` | a task is only enqueued once its `depends_on` tasks are DONE; on start it loads their handoff (D2) | correctness; requires the decomposer to actually populate `work_dependencies` (only 18 rows today — under-populated) |

*Why ▶ D3-b:* handoff is meaningless without ordering. **Sub-decision:** if the decomposer doesn't reliably emit dependencies, F11 must include making decomposition populate `work_dependencies` — otherwise there is no DAG to order by.

### D4 — ★ Pre-merge vs post-merge handoff (the governance-critical one)
| Option | A successor builds on… | Trade-off |
|---|---|---|
| **D4-a** Post-merge only | the predecessor's **Founder-merged** code on `main` | governance-clean (only approved code is built upon); **serializes the whole mission on Founder approvals** — with per-task Founder gates, a 5-task mission needs 5 approvals in sequence |
| **▶ D4-b** Pre-merge within a mission, Founder-gated at the mission edge | successor builds on the predecessor's **unmerged** in-mission branch/tree; the *mission's* PR(s) still require Founder merge before anything reaches `main` | keeps autonomy flowing inside a mission while preserving the Founder merge gate at the boundary; risk: intra-mission work builds on not-yet-approved code |
| **D4-c** Hybrid | post-merge across "milestones," pre-merge within a milestone | most control, most complexity |

*Why ▶ D4-b (tentative):* D4-a makes multi-task missions painfully serial given the existing per-task Founder gate; D4-b preserves the one gate that matters (nothing hits `main` unapproved) while letting a mission's internal tasks flow. **This is the decision I most want the Founder to rule on explicitly** — it trades governance strictness for mission throughput.

### D5 — Failure propagation (given 74% of tasks fail today)
| Option | If a predecessor fails | Trade-off |
|---|---|---|
| **D5-a** Block dependents | dependents never run | safe; a single early failure can stall the whole mission |
| **D5-b** Skip + continue | dependents run without the failed predecessor's handoff | throughput; dependents run blind (the very problem F11 fixes) |
| **▶ D5-c** Escalate to Founder (PROMPT-ESC) | pause the dependent chain, hand the Founder the failing task + six-field escalation, resume on decision | matches WES's existing escalation model; costs a Founder interruption |

*Why ▶ D5-c:* with today's failure rate, silent skip (D5-b) guarantees blind dependents; hard block (D5-a) stalls silently. Escalation keeps the Founder in the loop exactly when the DAG breaks.

---

## 3. Proposed v1 scope (contingent on D1–D5)

Assuming the ▶ defaults (D1-c, D2-b, D3-b, D4-b, D5-c), v1 would be **~3 scoped SOP-CODING PRs**, no schema change (reusing `work_dependencies`, `generated_changes`, `development_handoffs`):

1. **PR-1 — Dependency ordering:** topological scheduler over `work_dependencies`; decomposer populates dependencies; dependents enqueue only when predecessors are DONE. Escalate on predecessor failure (D5-c).
2. **PR-2 — Artifact manifest + injection:** a `HandoffManifest` builder that reads predecessors' `generated_changes` (files/symbols/PR ref) and injects it into the successor's context (`ContextBuilder`), token-bounded and budget-aware (WES-DEC-011).
3. **PR-3 — Shared mission workspace:** run a mission's tasks sequentially in one sandbox so successors start from the predecessor's committed tree (D1-c), with the Founder merge gate unchanged at the mission boundary (D4-b).

**Acceptance (design §D-style):** re-run a small 2-task mission where T2 depends on T1 (T1 creates `module.py`, T2 extends it). Prove: T2's composed context lists T1's file+symbol; T2's branch contains T1's code; the mission's PR(s) still require Founder merge; a forced T1 failure escalates instead of running T2 blind.

## 4. Guardrails (unchanged, non-negotiable)
- SOP-CODING per PR; coverage ≥ 71%; Founder-only merges (WES-DEC-002); honest 5-part reports.
- ATLAS working-tree files never staged/touched.
- The Founder merge gate to `main` is preserved regardless of D4.
- No mission may exceed its budget envelope (WES-DEC-011) — D2/D2-c token cost is bounded and metered.

## 5. What I need from the Founder
Rule on **D1, D2, D3, D4, D5** (D4 is the important one). On your rulings I will amend this doc with the decisions (F10-style), then build PR-1 → PR-2 → PR-3, each SOP-CODING and held for your merge. **No code is written until you decide.**
