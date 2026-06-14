from typing import Any, Dict
from packages.shared_types.models import SimulationState, AgentProposal

def _update_bp(bp_str: str, sys_delta: int, dia_delta: int) -> str:
    """Helper to adjust blood pressure fractions safely."""
    try:
        sys, dia = bp_str.split("/")
        return f"{max(70, int(sys) + sys_delta)}/{max(40, int(dia) + dia_delta)}"
    except Exception:
        return bp_str

def apply_proposal_transition(proposal: AgentProposal, state: SimulationState) -> Dict[str, Any]:
    """Apply deterministic simulation rules based on the resolved proposal and domain."""
    
    action_type = proposal.action_type.lower()
    recommended_action = proposal.recommended_action
    
    prev_stability = state.stability_score
    prev_risk = state.risk_level
    
    effect_label = "unchanged"
    summary = "No significant effect detected."
    
    if state.domain == "clinical":
        # Clinical Domain logic
        heart_rate = state.metrics.get("heart_rate", 38)
        oxygen_sat = state.metrics.get("oxygen_saturation", 89)
        pain_level = state.metrics.get("pain_level", 8)
        bp_str = state.metrics.get("blood_pressure", "86/54")
        
        if action_type == "escalate":
            state.stability_score = min(100, state.stability_score + 12)
            pain_level = max(0, pain_level - 2)
            oxygen_sat = min(99, oxygen_sat + 2)
            bp_str = _update_bp(bp_str, 8, 4)
            state.status_summary = "Urgent reperfusion activated; hemodynamics stabilizing under intensive care."
            effect_label = "improving"
            summary = "Timely escalation to catheterization laboratory improved cardiac perfusion and mitigated ongoing ischemia."
            
        elif action_type == "rhythm_support":
            state.stability_score = min(100, state.stability_score + 10)
            heart_rate = min(78, heart_rate + 14)
            bp_str = _update_bp(bp_str, 6, 4)
            state.status_summary = "Bradycardia actively supported; heart rate and pressure improved."
            effect_label = "improving"
            summary = "Rate-support therapy successfully elevated heart rate and perfusion pressures."
            
        elif action_type in {"supportive", "mitigate"}:
            state.stability_score = min(100, state.stability_score + 5)
            oxygen_sat = min(99, oxygen_sat + 1)
            pain_level = max(0, pain_level - 1)
            state.status_summary = "Receiving supportive STEMI therapy; remaining under close review."
            effect_label = "improving"
            summary = "Supportive supplemental oxygen and anticoagulation support yielded marginal hemodynamic improvements."
            
        elif action_type == "unsafe":
            state.stability_score = max(0, state.stability_score - 9)
            oxygen_sat = max(78, oxygen_sat - 2)
            pain_level = min(10, pain_level + 1)
            heart_rate = max(28, heart_rate - 4)
            bp_str = _update_bp(bp_str, -6, -4)
            state.status_summary = "Severe instability following an contraindicated or delayed action."
            effect_label = "worsening"
            summary = "Contraindicated recommendation exacerbated cardiac workload, worsening myocardial ischemia."
            
        else:  # monitor / general
            # Passive monitoring, potential decay if stability is low
            if state.stability_score < 40:
                state.stability_score = max(0, state.stability_score - 2)
                heart_rate = max(28, heart_rate - 1)
                bp_str = _update_bp(bp_str, -2, -1)
                state.status_summary = "Patient drifting; active therapeutic interventions required."
                effect_label = "worsening"
                summary = "Active monitoring without intervention allowed minor status deterioration."
            else:
                state.status_summary = "Under continuous observation; status remains stable but unchanged."
                effect_label = "unchanged"
                summary = "Continuous observation maintained; no clinical change."
                
        # Sync metrics back
        state.metrics["heart_rate"] = heart_rate
        state.metrics["oxygen_saturation"] = oxygen_sat
        state.metrics["pain_level"] = pain_level
        state.metrics["blood_pressure"] = bp_str
        
    elif state.domain == "disaster":
        # Disaster Response Domain logic
        containment = state.metrics.get("containment_rate", 15)
        hazmat = state.metrics.get("hazmat_ppm", 420)
        evac_pct = state.metrics.get("evacuation_percentage", 12)
        injured = state.metrics.get("injured_count", 6)
        
        if action_type == "mitigate":
            state.stability_score = min(100, state.stability_score + 15)
            containment = min(100, containment + 20)
            hazmat = max(10, hazmat - 80)
            state.status_summary = "Neutralizing fog successfully suppressing HCl vapor plume. Source leak sealing."
            effect_label = "improving"
            summary = "Deployment of aerosolized water and alkaline fog successfully neutralized vapor density and accelerated plume containment."
            
        elif action_type in {"escalate", "supportive"}:  # Evacuation / Perimeter
            state.stability_score = min(100, state.stability_score + 10)
            evac_pct = min(100, evac_pct + 25)
            hazmat = max(10, hazmat - 20)
            injured = max(0, injured - 1)
            state.status_summary = "Evacuation routing of Sector B progressing. Traffic perimeter barricaded."
            effect_label = "improving"
            summary = "Evacuation routing successfully cleared citizens from the east sector buffer zone."
            
        elif action_type == "unsafe":
            state.stability_score = max(0, state.stability_score - 12)
            hazmat = min(1000, hazmat + 60)
            injured = min(50, injured + 3)
            containment = max(0, containment - 5)
            state.status_summary = "Critical failure: evacuation routed windswards; toxic exposure rising."
            effect_label = "worsening"
            summary = "Unsafe evacuation layout routed civilians downwind into the toxic plume, causing acute respiratory admissions."
            
        else:  # monitor / general
            hazmat = min(1000, hazmat + 15)  # plume expands if idle
            if state.stability_score < 40:
                state.stability_score = max(0, state.stability_score - 3)
                injured = min(50, injured + 1)
                state.status_summary = "Plume continuing to disperse eastwards; chemical plume expanding."
                effect_label = "worsening"
                summary = "Plume dispersion continued unchecked; atmospheric concentration increased."
            else:
                state.status_summary = "Perimeters monitored; vapor plume density static."
                effect_label = "unchanged"
                summary = "Monitoring ongoing; vapor plume concentrations remain static."
                
        # Sync metrics back
        state.metrics["containment_rate"] = containment
        state.metrics["hazmat_ppm"] = hazmat
        state.metrics["evacuation_percentage"] = evac_pct
        state.metrics["injured_count"] = injured

    elif state.domain == "logistics":
        # Logistics Recovery Domain logic
        backlog = state.metrics.get("backlog_units", 2200)
        delay = state.metrics.get("routing_delay_hrs", 14)
        capacity = state.metrics.get("warehouse_capacity_percentage", 96)
        vessels = state.metrics.get("idle_vessels", 9)
        sla_violations = state.metrics.get("active_sla_violations", 45)
        
        if action_type == "mitigate":  # re-route
            state.stability_score = min(100, state.stability_score + 15)
            backlog = max(0, backlog - 400)
            delay = max(2, delay - 3)
            vessels = max(0, vessels - 2)
            state.status_summary = "Ocean carriers diverted to Port B. Cargo flows bypassing locks."
            effect_label = "improving"
            summary = "Alternative port routing successfully bypassed crane network lockout, restoring container flow."
            
        elif action_type in {"escalate", "supportive"}:  # capacity / pooling
            state.stability_score = min(100, state.stability_score + 10)
            capacity = max(50, capacity - 8)
            sla_violations = max(0, sla_violations - 10)
            state.status_summary = "Secondary motor carrier pool active. Warehousing buffers auditing."
            effect_label = "improving"
            summary = "Establishment of truck logistics pools eased storage bottleneck caps at backup depots."
            
        elif action_type == "unsafe":
            state.stability_score = max(0, state.stability_score - 10)
            backlog = min(10000, backlog + 500)
            delay = min(72, delay + 4)
            capacity = min(100, capacity + 3)
            sla_violations = min(200, sla_violations + 15)
            state.status_summary = "Severe bottlenecking; routing cargo into offline terminals."
            effect_label = "worsening"
            summary = "Directing additional truck freight into locks forced localized terminal congestion, triggering shipping delays."
            
        else:  # monitor / general
            backlog = min(10000, backlog + 100)  # backlog increases
            if state.stability_score < 40:
                state.stability_score = max(0, state.stability_score - 2)
                delay = min(72, delay + 1)
                state.status_summary = "Logistics stagnation continues; backups locking up rail nodes."
                effect_label = "worsening"
                summary = "Gridlock persisted; maritime backlog grew by another shipping tier."
            else:
                state.status_summary = "Freight flow static; monitoring backup network capacity."
                effect_label = "unchanged"
                summary = "Logistics flows observed; no traffic throughput changes."
                
        # Sync metrics back
        state.metrics["backlog_units"] = backlog
        state.metrics["routing_delay_hrs"] = delay
        state.metrics["warehouse_capacity_percentage"] = capacity
        state.metrics["idle_vessels"] = vessels
        state.metrics["active_sla_violations"] = sla_violations

    # --- Derive overall state outcome ---
    stability_delta = state.stability_score - prev_stability
    risk_worsened = (prev_risk != "critical" and state.risk_level == "critical")
    
    if stability_delta >= 5:
        state_outcome = "Improved"
    elif stability_delta <= -3 or risk_worsened:
        state_outcome = "Worsened"
    else:
        state_outcome = "Unchanged"
        
    state.state_outcome = state_outcome
    
    # Sync effect_label with state outcome to guarantee UI agreement
    effect_label = (
        "improving" if state_outcome == "Improved"
        else "worsening" if state_outcome == "Worsened"
        else "unchanged"
    )
    
    state.latest_change = summary
    state.timeline.append(summary)
    
    # Update risk level based on stability thresholds
    if state.stability_score >= 60:
        state.risk_level = "moderate"
    if state.stability_score >= 80:
        state.risk_level = "low"
    if state.stability_score < 45:
        state.risk_level = "high"
    if state.stability_score < 30:
        state.risk_level = "critical"
        
    # Append to completed interventions / decisions lists
    if action_type in {"escalate", "mitigate", "rhythm_support", "supportive"}:
        if recommended_action not in state.interventions_done:
            state.interventions_done.append(recommended_action)
            
    if recommended_action not in state.decisions_applied:
        state.decisions_applied.append(recommended_action)
        
    # Clean up pending actions list
    # Match fuzzy strings
    for pending in list(state.pending_actions):
        if any(keyword in recommended_action.lower() for keyword in pending.lower().split() if len(keyword) > 3):
            state.pending_actions.remove(pending)
            
    # Add new warnings/actions dynamically
    if action_type == "unsafe":
        remedy_action = "Remediate safety failure immediately"
        if remedy_action not in state.pending_actions:
            state.pending_actions.insert(0, remedy_action)
            
    # Ensure next actions are listed
    if not state.pending_actions:
        state.pending_actions.append("Re-evaluate general system conditions")
        
    return {
        "summary": summary,
        "effect_label": effect_label,
        "state_outcome": state_outcome
    }
