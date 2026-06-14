from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import uuid
import sys
import os

# Ensure package directories can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from packages.shared_types.models import (
    SessionSnapshot,
    SimulationState,
    EventSchema,
    OverrideRequest,
    AgentProposal
)
from packages.agents.registry import SCENARIOS
from packages.orchestration.engine import WorkflowGraphEngine

router = APIRouter()

# In-memory session store
# session_id -> { "domain": str, "scenario_name": str, "case_data": dict, "state": SimulationState, "events": List[EventSchema], "active_directive": str }
sessions: Dict[str, Dict[str, Any]] = {}

def get_operator_role_name(domain: str) -> str:
    """Return the professional command role name based on the active domain."""
    d = domain.lower()
    if d == "clinical":
        return "Attending Physician"
    elif d == "disaster":
        return "Incident Commander"
    else:
        return "Operations Director"

@router.post("/start", response_model=SessionSnapshot)
async def start_session(payload: Dict[str, str]):
    """Initialize an AegisFlow simulation session under a chosen operational domain."""
    domain = payload.get("domain", "clinical").lower()
    if domain not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unsupported domain: {domain}")
        
    session_id = str(uuid.uuid4())
    scenario = SCENARIOS[domain]
    
    # Initialize state
    init_state = scenario["initial_state"]
    sim_state = SimulationState(
        domain=domain,
        scenario_id=domain,
        status_summary=init_state["status_summary"],
        stability_score=init_state["stability_score"],
        risk_level=init_state["risk_level"],
        metrics=dict(init_state["metrics"]),
        interventions_done=list(init_state["interventions_done"]),
        decisions_applied=list(init_state["decisions_applied"]),
        pending_actions=list(init_state["pending_actions"]),
        latest_change=init_state["latest_change"],
        state_outcome=init_state["state_outcome"],
        timeline=list(init_state["timeline"])
    )
    
    # Seed introductory events
    intro_event = EventSchema(
        id="sys_init",
        role="system",
        display_name="AegisFlow Control",
        event_type="system_event",
        status="final",
        content=f"Simulation initialized. Core agents mobilized for {scenario['scenario_name']}.",
        state_change_summary=sim_state.latest_change
    )
    
    # Domain specific handoff dispatch
    if domain == "clinical":
        handoff_content = "Triage Alert: Patient reporting chest pain, bradycardia, low SpO2. Primary cardiac pathway activated."
        disp_name = "Triage Nurse"
        role_key = "nurse"
    elif domain == "disaster":
        handoff_content = "Hazmat Sensor Alert: Chemical detector array reports spikes in toxic HCl atmosphere downwind. Sector B under immediate threat."
        disp_name = "Telemetry Sensor"
        role_key = "nurse"
    else:
        handoff_content = "Alert: Port Central gateway servers report ransomware locks. Ship berthing and freight scheduling halting."
        disp_name = "Network Monitor"
        role_key = "nurse"
        
    handoff_event = EventSchema(
        id=f"evt_init_handoff_{uuid.uuid4()}",
        role=role_key,
        display_name=disp_name,
        event_type="proposal",
        status="final",
        content=handoff_content
    )
    
    events_list = [intro_event, handoff_event]
    
    # Save base session
    sessions[session_id] = {
        "domain": domain,
        "scenario_name": scenario["scenario_name"],
        "case_data": scenario["case_data"],
        "state": sim_state,
        "events": events_list,
        "active_directive": None
    }
    
    # Run the initial multi-agent workflow graph turn
    try:
        turn_snapshot = await WorkflowGraphEngine.execute_step(
            session_id=session_id,
            domain=domain,
            state=sim_state,
            active_directive=None
        )
        
        # Merge new events and state updates into session storage
        sessions[session_id]["events"].extend(turn_snapshot.events)
        sessions[session_id]["state"] = turn_snapshot.simulation_state
        
    except Exception as e:
        # Fallback system log event
        err_event = EventSchema(
            id=f"evt_err_{uuid.uuid4()}",
            role="system",
            display_name="Pipeline Error",
            event_type="system_event",
            status="final",
            content=f"Workflow graph execution failed: {e}. Check server logs or configure GEMINI_API_KEY for real LLM evaluations."
        )
        sessions[session_id]["events"].append(err_event)
        
    # Build complete response snapshot
    s = sessions[session_id]
    return SessionSnapshot(
        session_id=session_id,
        domain=s["domain"],
        scenario_name=s["scenario_name"],
        case_data=s["case_data"],
        events=s["events"],
        active_directive=s["active_directive"],
        safety_flags=s["state"].metrics.get("flags", []),
        next_action=s["state"].pending_actions[0] if s["state"].pending_actions else "Monitor general conditions",
        simulation_state=s["state"]
    )

@router.get("/{session_id}/events", response_model=SessionSnapshot)
async def get_session_details(session_id: str):
    """Retrieve cumulative simulation log events and state snapshot for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    s = sessions[session_id]
    return SessionSnapshot(
        session_id=session_id,
        domain=s["domain"],
        scenario_name=s["scenario_name"],
        case_data=s["case_data"],
        events=s["events"],
        active_directive=s["active_directive"],
        safety_flags=s["state"].metrics.get("flags", []),
        next_action=s["state"].pending_actions[0] if s["state"].pending_actions else "Monitor general conditions",
        simulation_state=s["state"]
    )

@router.post("/{session_id}/override", response_model=SessionSnapshot)
async def inject_operator_override(session_id: str, req: OverrideRequest):
    """Inject a human commander directive and re-trigger revised multi-agent reviews."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    directive = req.directive.strip()
    if not directive:
        raise HTTPException(status_code=400, detail="Override directive must not be empty.")
        
    s = sessions[session_id]
    s["active_directive"] = directive
    
    # 1. Append override directive event to timeline
    operator_role = get_operator_role_name(s["domain"])
    override_event = EventSchema(
        id=f"evt_override_{uuid.uuid4()}",
        role="human",
        display_name=operator_role,
        event_type="override",
        status="final",
        content=f"**Command Directive**: {directive}"
    )
    s["events"].append(override_event)
    
    # 2. Re-run multi-agent pipeline with override active
    try:
        turn_snapshot = await WorkflowGraphEngine.execute_step(
            session_id=session_id,
            domain=s["domain"],
            state=s["state"],
            active_directive=directive
        )
        
        # Merge new events and state updates into session storage
        s["events"].extend(turn_snapshot.events)
        s["state"] = turn_snapshot.simulation_state
        
    except Exception as e:
        err_event = EventSchema(
            id=f"evt_err_{uuid.uuid4()}",
            role="system",
            display_name="Pipeline Error",
            event_type="system_event",
            status="final",
            content=f"Workflow graph execution failed during override check: {e}."
        )
        s["events"].append(err_event)
        
    return SessionSnapshot(
        session_id=session_id,
        domain=s["domain"],
        scenario_name=s["scenario_name"],
        case_data=s["case_data"],
        events=s["events"],
        active_directive=s["active_directive"],
        safety_flags=s["state"].metrics.get("flags", []),
        next_action=s["state"].pending_actions[0] if s["state"].pending_actions else "Monitor general conditions",
        simulation_state=s["state"]
    )
