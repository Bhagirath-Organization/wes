/* Founder API — thin client over the existing backend Founder OS / Mission Control
   / Company Evolution endpoints. No backend change; reuses the shared http client. */
import { http } from "./client";

export interface MissionSummary {
  mission_id: string;
  mission_name: string;
  business_objective: string | null;
  current_stage: string;
  overall_progress: number;
  business_confidence: number | null;
  status: string;
}
export interface MissionsResponse {
  missions: MissionSummary[];
  total: number;
  lifecycle: string[];
}

export interface MissionDashboard {
  mission_name: string;
  mission_description: string | null;
  business_objective: string | null;
  business_value: string | null;
  current_stage: string;
  overall_progress: number;
  current_executive: string;
  current_department: string;
  current_activity: string;
  current_risk: string | null;
  current_blockers: string[];
  expected_completion: string;
  current_confidence: number;
  business_impact: string | null;
  next_executive_action: string;
  pending_founder_decision: { decision: string; type: string } | null;
  latest_executive_report: Record<string, unknown>;
  final_deliverables: string[];
  deployment_status: string;
  live_url: string | null;
  business_timeline: { stage: string; state: string }[];
  explanation: {
    what_happened: string;
    why: string;
    what_happens_next: string;
    founder_action_required: boolean;
  };
}

export interface CompanyHealth {
  company_health_score: number | null;
  overall: string | null;
  executive_confidence: string | null;
  quality_health: string | null;
  deployment_health: string | null;
  knowledge_health: string | null;
  memory_health: string | null;
  provider_health: string | null;
  mission_success_rate: number | null;
  learning_active: string | null;
  blueprint_compliance: string | null;
  note: string | null;
}

export interface FounderDecision {
  kind: string;
  title: string;
  why?: string;
  project?: string;
  project_id?: string;
  action?: string;
}

export interface EvolutionOpportunity {
  recommendation: string;
  business_value: string | null;
  expected_benefit: string | null;
  estimated_risk: string | null;
  priority: string;
  approval_required: boolean;
}
export interface EvolutionView {
  company_evolution_score: number;
  top_opportunities: EvolutionOpportunity[];
  note: string;
}

export interface ExecMessage {
  speaker: string;
  speaker_title: string;
  answer: string;
  reasoning_summary?: string;
  business_impact?: string | null;
  recommendation?: string | null;
  confidence?: number;
  next_action?: string | null;
  approval_required?: boolean;
}
export interface ExecBrief {
  speaker: string; speaker_title: string; greeting: string; message: string;
  recommendations: string[]; follow_up: string; suggested_questions: string[];
}
export interface ExecInvite {
  joined: boolean; executive?: string; speaker: string; speaker_title: string;
  name?: string; join_message?: string; opening?: string; focus?: string; message?: string;
}
export interface ExecMeeting {
  topic: string;
  opinions: { executive: string; title: string; opinion: string }[];
  final_recommendation: string; decision_required: boolean;
}
export interface ExecStatus {
  current_executive: string; current_mission: string | null; current_thinking: string;
  current_risk: string | null; current_confidence: number;
  company_health: string | null; company_health_score: number | null;
}

export interface LiveExecutive {
  executive: string; status: string; thinking: string; objective: string | null;
  stage: string | null; confidence: number | null; eta: string | null;
}
export interface LiveCompany {
  executives: LiveExecutive[]; active_missions: number;
  company_health: string | null; company_health_score: number | null;
}
export interface MissionDetail {
  overview: {
    mission_name: string; business_goal: string | null; business_value: string | null;
    business_stage: string; current_executive: string; current_department: string;
    current_activity: string; confidence: number; progress: number; health: string;
    expected_completion: string; business_impact: string | null; deployment_status: string;
    explanation: { what_happened: string; why: string; what_happens_next: string; founder_action_required: boolean };
  };
  stages: { stage: string; state: string }[];
  map: { roles: string[]; current: string; position: number };
  discussions: { executive: string; kind: string; message: string }[];
  brain: { knows: string[]; assumptions: string[]; evidence: string[]; blueprint_guidance: string[]; previous_projects: string[] };
  risks: { risk: string; category: string; probability: string; impact: string; owner: string; mitigation: string; confidence: number }[];
  decisions: {
    pending_executive: { decision: string | null; rationale: string; open_concerns: string[] } | null;
    pending_founder: { decision: string; type: string } | null;
    recommended: string; business_consequences: string; alternatives: string[];
  };
  timeline: { activity: string; outcome: string; by: string }[];
}
export interface MissionAnalytics {
  throughput: { total: number; active: number; delivered: number };
  mission_confidence: number | null;
  decision_bottleneck: number;
  executive_workload: { executive: string; missions: number }[];
  stage_distribution: { stage: string; count: number }[];
  business_value_delivered: number;
}

export interface BrainHome {
  thinking_topics: { mission_id: string; topic: string; executive: string; activity: string; confidence: number; stage: string }[];
  references: Record<string, number>;
  current_recommendation: string | null;
  evolution_score: number | null;
  company_health: string | null;
  thinking_stream: { executive: string; event: string }[];
}
export interface BrainMission {
  mission_name: string | null;
  reasoning: {
    business_context: string; objectives: string[]; known_facts: string[]; evidence: string[];
    unknowns: string[]; assumptions: string[];
    alternatives: { option: string; summary: string; chosen: boolean }[];
    final_recommendation: string; confidence: number; business_impact: string;
    expected_risks: string[]; why_alternatives_rejected: string[];
  };
  decision_explainer: { why_this: string; why_not_other: string; why_confidence: string; missing_information: string[]; what_would_change_it: string[] };
  blueprint: { volumes_guiding: { volume: string; why: string }[]; compliance_percentage: number | null; missing_requirements: string[]; conflicts: string[]; recommendations: string[] };
  domain: Record<string, unknown>;
  memory: { similar_projects: { objective: string; similarity: number }[]; categories: Record<string, number>; total_remembered: number };
  repository: { reusable_capabilities: { capability: string; why: string }[]; existing_modules: string[]; potential_reuse: string[]; technical_debt: string; business_impact: string };
  graph: { nodes: { id: string; label: string; group: string }[]; edges: { from: string; to: string }[] };
}
export interface BrainMemory {
  total: number; by_category: { category: string; count: number }[];
  recent: { summary: string; category: string }[]; mistakes_avoided: string[];
}
export interface BrainLearning {
  learning_rules: number; new_knowledge: string[]; patterns_discovered: string[];
  emerging_opportunities: string[]; knowledge_gaps: string[]; learning_score: number | null; evolution_score: number | null;
}
export interface BrainSearch {
  query: string; total: number;
  results: {
    missions: { id: string; title: string; stage: string }[];
    knowledge: { title: string; similarity: number }[];
    previous_projects: { title: string; similarity: number }[];
    risks: { title: string }[];
    recommendations: { title: string }[];
  };
}

export interface WorkforceMember {
  id: string; name: string; role: string; department: string; status: string;
  availability: string; current_work: string; current_mission: string | null;
  confidence: number; missions_leading: string[]; activity_count: number; knowledge: number;
}
export interface WorkforceHome {
  teams: { department: string; members: WorkforceMember[] }[];
  summary: { total: number; working: number; available: number; overloaded: string[]; departments: number };
}
export interface EmployeeProfile {
  name: string; role: string; department: string; reports_to: string;
  responsibilities: string[]; skills: { primary: string; secondary: string[]; domains: string[] };
  status: string; availability: string; current_mission: string | null; current_work: string;
  average_confidence: number; mission_history: string[]; recent_decisions: string[];
  knowledge_areas: string[];
  performance: { completed: number; contributions: number; approval_rate: number | null; quality: string; knowledge_items: number };
  collaboration: { with: string; frequency: number }[]; last_activity: string;
  learning: { trend: string; score: number | null; recent: string[] };
}
export interface OrgChart { nodes: { id: string; label: string; sub: string; group: string }[]; edges: { from: string; to: string }[] }
export interface CollabNetwork { nodes: { id: string; label: string }[]; edges: { from: string; to: string; strength: number; frequency: number }[]; note: string }
export interface HiringPipeline { future_roles: { role: string; reason: string; business_value: string; expected_impact: string; status: string }[]; note: string }

export interface KnowledgeHome {
  metrics: { knowledge_health: string; total_knowledge: number; growth_7d: number; coverage_areas: number;
    confidence: number; quality: string; reuse_rate: number; gaps: number; freshness: number; ageing: number;
    learning_score: number | null; trend: string };
  recent_learnings: { headline: string; area: string; confidence: number }[];
  most_valuable: { title: string; area: string; confidence: number; value: number }[];
  contributing_missions: { mission: string; learnings: number }[];
  fastest_growing_domain: { domain: string; new_items: number } | null;
}
export interface KnowledgeReuse {
  frequently_reused: { knowledge: string; used: number }[]; never_reused: string[];
  reuse_rate: number; recommended_consolidation: string[]; opportunities: string[];
}
export interface KnowledgeMemory {
  lessons_remembered: string[]; mistakes_avoided: string[];
  repeated_patterns: { pattern: string; seen: number }[]; institutional_knowledge: { title: string; value: number }[];
  ageing: { stale_count: number; stale_examples: string[] }; confidence: number;
}
export interface KnowledgeInsights {
  most_valuable_learning: string | null; fastest_growing_domain: { domain: string; new_items: number } | null;
  emerging_opportunities: string[]; knowledge_at_risk: string[]; requires_validation: string[]; requires_founder_approval: string[];
}
export interface KnowledgeCollab {
  network: { nodes: { id: string; label: string }[]; edges: { from: string; to: string; strength: number; frequency: number }[] };
  contributions: { contributor: string; knowledge: number }[]; note: string;
}
export interface KnowledgeGraph { nodes: { id: string; label: string; group: string }[]; edges: { from: string; to: string }[] }

export interface CmdKpi { value: number | null; label: string | null; trend: string }
export interface CmdOverview {
  kpis: Record<string, CmdKpi>;
  attention: { kind: string; text: string; urgency: string }[];
}
export interface CmdBrief { greeting: string; yesterday: string[]; today_priorities: string[]; closing: string }
export interface CmdScoreboard {
  executives: { executive: string; responsibility: string; health: string; workload: number;
    confidence: number; mission_ownership: string[]; pending_decisions: number; business_impact: string; trend: string }[];
}
export interface CmdDecisions {
  decisions: { id: string | null; title: string; kind: string; recommendation: string; business_impact: string;
    urgency: string; alternatives: string[]; expected_outcome: string; actions: string[] }[];
  total: number;
}
export interface CmdPredictions { insights: { prediction: string; type: string; confidence: number }[] }
export interface CmdHealth { overall: string | null; score: number | null; areas: { area: string; health: string; trend: string; confidence: number; owner: string }[] }
export interface CmdBI { kpis: { kpi: string; value: number | null; unit: string }[] }
export interface CmdTimeline { events: { headline: string; kind: string }[] }
export interface CmdRisks { risks: { risk: string; category: string; owner: string; trend: string; confidence: number; mitigation: string }[]; by_category: { category: string; count: number }[] }
export interface CmdOpportunities {
  high_value_improvements: { title: string; value: string | null; approval: boolean }[];
  fast_growing_domains: (string | null)[]; reuse_rate: number | null;
  future_hiring: { role: string; value: string }[];
}

export interface OpItem { operation: string; owner: string; status: string; progress: number; note: string | null }
export interface OpQueue {
  running: OpItem[]; queued: OpItem[]; blocked: OpItem[]; waiting_for_founder: OpItem[];
  completed_recently: OpItem[]; cancelled: OpItem[]; deferred: OpItem[];
  summary: Record<string, number>;
}
export interface OpDecisions {
  total_autonomous: number; company_level: number; board_level: number; founder_level: number;
  recent: { decision: string; made_by: string; reason: string; confidence: number; business_impact: string; approval_policy: string }[];
}
export interface OpPolicy { levels: { level: number; name: string; scope: string[]; why: string }[] }
export interface OpActivity { events: { headline: string; detail: string; severity: string; kind: string; count: number }[] }
export interface OpAutonomy { executives: { executive: string; current_initiative: string; delegated_work: number; self_created_improvements: string[]; escalations: number; recommendations: string[]; completed_work: string }[] }
export interface OpPolicies { policies: { policy: string; rule: string; owner: string }[] }
export interface OpEscalations { escalations: { type: string; text: string; severity: string; owner: string }[]; total: number }
export interface OpAutomation { automated_processes: { process: string; runs: number; hours_saved: number }[]; time_saved_hours: number; manual_work_eliminated: string; automation_confidence: number; business_impact: string }
export interface OpTrust { autonomous_decisions: number; founder_overrides: number; founder_approvals: number; executive_accuracy: number; recommendation_accuracy: number; decision_confidence: number; learning_trend: string; evolution_score: number | null; note: string }

export interface FactoryProduct {
  product_id: string; product: string; business_objective: string | null; current_stage: string;
  stage_blurb: string; current_executive: string; delivery_confidence: number | null;
  expected_delivery: string | null; business_value: string; current_risk: string | null;
  dependencies: string[]; founder_approval_status: string; progress: number; priority: string;
}
export interface FactoryPipeline { products: FactoryProduct[]; active: number; awaiting_founder: number; total: number }
export interface FactoryStage { stage: string; blurb: string; products: number; product_names: string[] }
export interface FactoryDelivery { stages: FactoryStage[]; total_in_flight: number }
export interface FactoryBuild {
  product: string; business_objective: string | null; current_progress: number; current_stage: string;
  what_is_happening: string; why: string; who_is_responsible: string; confidence: number | null;
  expected_outcome: string[]; business_impact: string | null; expected_delivery: string | null;
  current_risk: string | null; timeline: { stage: string; state: string }[]; founder_decision: unknown;
}
export interface FactoryQuality {
  products_passing: number; products_requiring_attention: number; quality_trend: string;
  review_quality: number; regression_confidence: number; release_confidence: number;
  average_score: number; reviews_performed?: number; note: string;
}
export interface FactoryReleases {
  upcoming_releases: { release: string; channel?: string; status: string }[];
  completed_releases: { release: string; channel?: string; status: string }[];
  delayed_releases: { release: string; status: string }[];
  blocked_releases: { release: string; status: string; note?: string }[];
  business_readiness: number; deployment_readiness: number; rollback_confidence: number; note: string;
}
export interface FactoryDependencies {
  products: { product: string; executive_owner: string; shared_capabilities: string[]; risk: string | null }[];
  shared_capabilities: { capability: string; used_by: string[] }[];
  knowledge_reuse: { reuse_rate: number | null; assets_reused: number | null; note: string };
  risks: { product: string; risk: string }[];
}
export interface FactoryFloor { stations: { who: string; activity: string; state: string }[]; live: boolean; active_operations: number; note: string }
export interface FactoryPortfolioItem { product: string; business_objective: string | null; business_value: string; priority: string }
export interface FactoryPortfolio {
  active: FactoryPortfolioItem[]; completed: FactoryPortfolioItem[]; paused: FactoryPortfolioItem[];
  planned: FactoryPortfolioItem[]; cancelled: FactoryPortfolioItem[];
  summary: Record<string, number>; business_value_delivered: number; strategic_alignment: number;
}

interface Data<T> { data: T }

export const founderApi = {
  missions: () => http.get<Data<MissionsResponse>>("/founder/missions").then((r) => r.data),
  mission: (id: string) => http.get<Data<MissionDashboard>>(`/founder/missions/${id}`).then((r) => r.data),
  timeline: (id: string) =>
    http.get<Data<{ events: { activity: string; outcome: string; by: string }[]; total_activities: number }>>(
      `/founder/missions/${id}/timeline`,
    ).then((r) => r.data),
  companyHealth: () => http.get<Data<CompanyHealth>>("/founder/company-health").then((r) => r.data),
  decisions: () =>
    http.get<Data<{ total: number; items: FounderDecision[] }>>("/founder/decisions").then((r) => r.data),
  evolution: () => http.get<Data<EvolutionView>>("/founder/evolution").then((r) => r.data),
  inbox: () => http.get<Data<Record<string, unknown>>>("/founder/inbox").then((r) => r.data),
  submitObjective: (objective: string) =>
    http.post<Data<{ project_id: string; code: string; objective: string; planned: boolean }>>(
      "/founder/objectives",
      { objective, auto_plan: false },
    ).then((r) => r.data),

  // Executive Office (Sprint 02)
  brief: () => http.get<Data<ExecBrief>>("/founder/executive/brief").then((r) => r.data),
  ask: (question: string, speaker?: string) =>
    http.post<Data<ExecMessage>>("/founder/executive/ask", { question, speaker }).then((r) => r.data),
  invite: (executive: string) =>
    http.post<Data<ExecInvite>>("/founder/executive/invite", { executive }).then((r) => r.data),
  meeting: (topic?: string) =>
    http.post<Data<ExecMeeting>>("/founder/executive/meeting", { topic }).then((r) => r.data),
  execStatus: () => http.get<Data<ExecStatus>>("/founder/executive/status").then((r) => r.data),

  // Mission Center (Sprint 03)
  live: () => http.get<Data<LiveCompany>>("/founder/live").then((r) => r.data),
  missionDetail: (id: string) => http.get<Data<MissionDetail>>(`/founder/missions/${id}/detail`).then((r) => r.data),
  missionAnalytics: () => http.get<Data<MissionAnalytics>>("/founder/mission-analytics").then((r) => r.data),

  // Company Brain (Sprint 04)
  brainHome: () => http.get<Data<BrainHome>>("/founder/brain/home").then((r) => r.data),
  brainMission: (id: string) => http.get<Data<BrainMission>>(`/founder/brain/mission/${id}`).then((r) => r.data),
  brainMemory: () => http.get<Data<BrainMemory>>("/founder/brain/memory").then((r) => r.data),
  brainLearning: () => http.get<Data<BrainLearning>>("/founder/brain/learning").then((r) => r.data),
  brainSearch: (q: string) => http.get<Data<BrainSearch>>(`/founder/brain/search?q=${encodeURIComponent(q)}`).then((r) => r.data),

  // AI Workforce (Sprint 05)
  workforceHome: () => http.get<Data<WorkforceHome>>("/founder/workforce/home").then((r) => r.data),
  employee: (id: string) => http.get<Data<EmployeeProfile>>(`/founder/workforce/employee/${id}`).then((r) => r.data),
  orgChart: () => http.get<Data<OrgChart>>("/founder/workforce/org-chart").then((r) => r.data),
  collaboration: () => http.get<Data<CollabNetwork>>("/founder/workforce/collaboration").then((r) => r.data),
  hiring: () => http.get<Data<HiringPipeline>>("/founder/workforce/hiring").then((r) => r.data),
  workforceSearch: (q: string) => http.get<Data<{ query: string; results: { id: string; name: string; role: string; department: string }[]; total: number }>>(`/founder/workforce/search?q=${encodeURIComponent(q)}`).then((r) => r.data),

  // Knowledge Network (Sprint 06)
  knHome: () => http.get<Data<KnowledgeHome>>("/founder/knowledge-network/home").then((r) => r.data),
  knGraph: () => http.get<Data<KnowledgeGraph>>("/founder/knowledge-network/graph").then((r) => r.data),
  knTimeline: () => http.get<Data<{ events: { headline: string; area: string; by: string; confidence: number }[] }>>("/founder/knowledge-network/timeline").then((r) => r.data),
  knMemory: () => http.get<Data<KnowledgeMemory>>("/founder/knowledge-network/memory").then((r) => r.data),
  knReuse: () => http.get<Data<KnowledgeReuse>>("/founder/knowledge-network/reuse").then((r) => r.data),
  knInsights: () => http.get<Data<KnowledgeInsights>>("/founder/knowledge-network/insights").then((r) => r.data),
  knCollaboration: () => http.get<Data<KnowledgeCollab>>("/founder/knowledge-network/collaboration").then((r) => r.data),
  knSearch: (q: string) => http.get<Data<BrainSearch>>(`/founder/knowledge-network/search?q=${encodeURIComponent(q)}`).then((r) => r.data),

  // Founder Command Center (Sprint 07)
  cmdOverview: () => http.get<Data<CmdOverview>>("/founder/command/overview").then((r) => r.data),
  cmdBrief: () => http.get<Data<CmdBrief>>("/founder/command/brief").then((r) => r.data),
  cmdScoreboard: () => http.get<Data<CmdScoreboard>>("/founder/command/scoreboard").then((r) => r.data),
  cmdMissionPerformance: () => http.get<Data<{ forecast: string; completion_rate: number; blocked_missions: number }>>("/founder/command/mission-performance").then((r) => r.data),
  cmdDecisions: () => http.get<Data<CmdDecisions>>("/founder/command/decisions").then((r) => r.data),
  cmdPredictions: () => http.get<Data<CmdPredictions>>("/founder/command/predictions").then((r) => r.data),
  cmdHealth: () => http.get<Data<CmdHealth>>("/founder/command/health").then((r) => r.data),
  cmdBI: () => http.get<Data<CmdBI>>("/founder/command/business-intelligence").then((r) => r.data),
  cmdTimeline: () => http.get<Data<CmdTimeline>>("/founder/command/timeline").then((r) => r.data),
  cmdRisks: () => http.get<Data<CmdRisks>>("/founder/command/risks").then((r) => r.data),
  cmdOpportunities: () => http.get<Data<CmdOpportunities>>("/founder/command/opportunities").then((r) => r.data),
  cmdSearch: (q: string) => http.get<Data<BrainSearch>>(`/founder/command/search?q=${encodeURIComponent(q)}`).then((r) => r.data),

  // Autonomous Operations (Sprint 08)
  opQueue: () => http.get<Data<OpQueue>>("/founder/operations/queue").then((r) => r.data),
  opDecisions: () => http.get<Data<OpDecisions>>("/founder/operations/autonomous-decisions").then((r) => r.data),
  opPolicy: () => http.get<Data<OpPolicy>>("/founder/operations/policy").then((r) => r.data),
  opActivity: () => http.get<Data<OpActivity>>("/founder/operations/activity").then((r) => r.data),
  opAutonomy: () => http.get<Data<OpAutonomy>>("/founder/operations/executive-autonomy").then((r) => r.data),
  opPolicies: () => http.get<Data<OpPolicies>>("/founder/operations/policies").then((r) => r.data),
  opEscalations: () => http.get<Data<OpEscalations>>("/founder/operations/escalations").then((r) => r.data),
  opAutomation: () => http.get<Data<OpAutomation>>("/founder/operations/automation").then((r) => r.data),
  opTrust: () => http.get<Data<OpTrust>>("/founder/operations/trust").then((r) => r.data),

  // Software Factory (Sprint 09)
  factoryProducts: () => http.get<Data<FactoryPipeline>>("/founder/factory/products").then((r) => r.data),
  factoryDelivery: () => http.get<Data<FactoryDelivery>>("/founder/factory/delivery-pipeline").then((r) => r.data),
  factoryBuild: (id: string) => http.get<Data<FactoryBuild>>(`/founder/factory/build/${id}`).then((r) => r.data),
  factoryQuality: () => http.get<Data<FactoryQuality>>("/founder/factory/quality").then((r) => r.data),
  factoryReleases: () => http.get<Data<FactoryReleases>>("/founder/factory/releases").then((r) => r.data),
  factoryDependencies: () => http.get<Data<FactoryDependencies>>("/founder/factory/dependencies").then((r) => r.data),
  factoryFloor: () => http.get<Data<FactoryFloor>>("/founder/factory/floor").then((r) => r.data),
  factoryPortfolio: () => http.get<Data<FactoryPortfolio>>("/founder/factory/portfolio").then((r) => r.data),
};
