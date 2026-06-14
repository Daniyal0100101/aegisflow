export interface AgentProposal {
  recommended_action: string;
  short_reason: string;
  urgency: string; // critical | high | moderate | low
  expected_effect?: string;
  target_metric: string;
  action_type: string;
  effect_label: string; // improving | worsening | unchanged
}

export interface ReviewReport {
  safety_flags: string[];
  confidence_score: number;
  criticism: string;
  suggested_modification?: string;
  is_approved: boolean;
}

export interface ExecutionStep {
  node_name: string;
  status: string; // pending | running | completed | failed
  output_summary?: string;
  timestamp: string;
  duration_ms?: number;
}

export interface SimulationState {
  domain: string;
  scenario_id: string;
  status_summary: string;
  stability_score: number;
  risk_level: string; // critical | high | moderate | low
  metrics: Record<string, any>;
  interventions_done: string[];
  decisions_applied: string[];
  pending_actions: string[];
  latest_change: string;
  state_outcome: "Improved" | "Worsened" | "Unchanged";
  timeline: string[];
}

export interface EventSchema {
  id: string;
  timestamp: string;
  role: "expert_1" | "expert_2" | "critic" | "orchestrator" | "system" | "human" | "nurse";
  display_name: string;
  event_type: "proposal" | "review" | "orchestration" | "state_update" | "override" | "system_event";
  content: string;
  status: string;
  action_metadata?: AgentProposal;
  review_metadata?: ReviewReport;
  state_change_summary?: string;
  execution_steps?: ExecutionStep[];
}

export interface SessionSnapshot {
  session_id: string;
  domain: string;
  scenario_name: string;
  case_data: Record<string, any>;
  events: EventSchema[];
  active_directive: string | null;
  safety_flags: string[];
  next_action: string;
  simulation_state: SimulationState;
}

export const PRESET_DIRECTIVES: Record<string, string[]> = {
  clinical: [
    "Hold anticoagulation immediately",
    "Activate catheterization lab",
    "Verify beta-blockers held",
    "Prepare intravenous pacemaker line",
  ],
  disaster: [
    "Dike water curtains to prevent sewer acid runoff",
    "Deploy additional hazmat blockades at Sector B",
    "Evacuate downstream Sector C sectors",
    "Dispatch auxiliary neutralizer crews",
  ],
  logistics: [
    "Route container ship diversion to Port B terminals",
    "Hold inventory dispatch at Depot 1 for audit",
    "Mobilize backup motor carrier trucking pools",
    "Audit storage limits at regional logistics terminals",
  ],
};
