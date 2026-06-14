import asyncio
import os
import json
import re
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from packages.shared_types.models import (
    SessionSnapshot,
    SimulationState,
    EventSchema,
    AgentProposal,
    ReviewReport,
    ExecutionStep
)
from packages.agents.registry import SCENARIOS, DOMAIN_AGENTS
from packages.state_engine.rules import apply_proposal_transition
from packages.evaluation.scoring import generate_confidence_profile
# Configuration for Google GenAI Client
_client = None

def _get_genai_client():
    global _client
    if _client is not None:
        return _client
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=key)
        return _client
    except Exception as e:
        print(f"[AegisFlow] Failed to initialize google-genai SDK: {e}")
        return None

def _call_gemini_api(prompt: str, temperature: float = 0.2) -> str:
    """Execute Gemini prompt using the new official Google GenAI Python library (google-genai) natively."""
    client = _get_genai_client()
    if not client:
        raise ValueError("Google GenAI client configuration failed or API key missing.")

    try:
        # Using gemini-3-flash as the recommended current model
        response = client.models.generate_content(
            model="gemini-3-flash",
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": 1000
            }
        )
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini SDK Client Error: {e}")

def _parse_proposal_response(text: str) -> Dict[str, str]:
    """Defensively parse structured specialist proposals from text output."""
    def extract(label: str) -> str:
        pattern = rf"{label}:\s*(.+?)(?=\n[A-Z][A-Za-z_ ]+?:|\Z)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        return " ".join(match.group(1).strip().split()) if match else ""

    action = extract("Recommended Action")
    reason = extract("Short Reason")
    urgency = extract("Urgency").lower() or "moderate"
    effect = extract("Expected Effect")
    target = extract("Target Metric")
    atype = extract("Action Type")
    
    if not action:
        # Fallback if unformatted
        lines = [line.strip("-* ").strip() for line in text.splitlines() if line.strip()]
        action = lines[0] if lines else "Continue continuous monitoring"
    if not reason:
        reason = "Deduced from specialist response."
    if not target:
        target = "stability"
    if not atype:
        # Simple keywords classification
        norm = action.lower()
        if any(w in norm for w in ["cath", "pci", "escalat", "divert", "evacuate", "blockade"]):
            atype = "escalate" if "cath" in norm or "pci" in norm else "mitigate"
        elif any(w in norm for w in ["atropine", "pacing", "neutralize", "spray"]):
            atype = "rhythm_support" if "atropine" in norm else "mitigate"
        elif any(w in norm for w in ["beta-blocker", "delay", "hold"]):
            atype = "unsafe"
        else:
            atype = "supportive"
            
    return {
        "recommended_action": action,
        "short_reason": reason,
        "urgency": urgency,
        "expected_effect": effect,
        "target_metric": target,
        "action_type": atype
    }

def _parse_review_response(text: str) -> Dict[str, Any]:
    """Parse review criticism report from text."""
    def extract(label: str) -> str:
        pattern = rf"{label}:\s*(.+?)(?=\n[A-Z][A-Za-z_ ]+?:|\Z)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        return " ".join(match.group(1).strip().split()) if match else ""
        
    critique = extract("Criticism")
    mod = extract("Suggested Modification")
    flags_str = extract("Safety Flags")
    score_str = extract("Confidence Score")
    
    flags = [f.strip("-* ").strip() for f in flags_str.split(",") if f.strip()] if flags_str else []
    
    try:
        score = int(re.search(r"\d+", score_str).group())
    except Exception:
        score = 80
        
    is_approved = len(flags) == 0
    
    return {
        "criticism": critique or "Proposals verified under safety constraints.",
        "suggested_modification": mod,
        "safety_flags": flags,
        "confidence_score": score,
        "is_approved": is_approved
    }

# ----------------- Sandbox Fallback Data Generator -----------------
def _get_sandbox_fallback(domain: str, directive: Optional[str] = None) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Any], Dict[str, str]]:
    """Generate high-fidelity mock reports for offline development or API limits."""
    d_lower = domain.lower()
    
    if d_lower == "clinical":
        if not directive:
            exp1 = {
                "recommended_action": "Activate catheterization laboratory for urgent coronary angiography and PCI",
                "short_reason": "Acute anterior STEMI with hemodynamically unstable bradycardia requires reperfusion.",
                "urgency": "critical",
                "expected_effect": "Re-establish coronary patency and restore myocardial contractility.",
                "target_metric": "stability",
                "action_type": "escalate"
            }
            exp2 = {
                "recommended_action": "Administer Atropine 0.5mg IV push, repeat up to 3mg, and hold all beta-blockers",
                "short_reason": "Support heart rate and blood pressure while preparation for PCI is finalized.",
                "urgency": "critical",
                "expected_effect": "Temporarily elevate sinus node automaticity and systemic perfusion.",
                "target_metric": "heart_rate",
                "action_type": "rhythm_support"
            }
            critic = {
                "criticism": "Atropine is highly appropriate for bradycardic STEMI to bridge to PCI. Thrombolytics are omitted given PCI possibility. No major safety blocks.",
                "suggested_modification": "Ensure intravenous pacing electrodes are attached in case atropine fails.",
                "safety_flags": [],
                "confidence_score": 92,
                "is_approved": True
            }
            orch = {
                "recommended_action": "Activate cath lab and administer Atropine 0.5mg IV immediately",
                "short_reason": "Urgent PCI is the primary goal; pharmacological pacing with atropine bridges the perfusion deficit.",
                "urgency": "critical",
                "expected_effect": "Elevate heart rate to >50 bpm and prep for angiography.",
                "target_metric": "stability",
                "action_type": "escalate"
            }
        else:
            dir_norm = directive.lower()
            if "hold anticoag" in dir_norm or "heparin" in dir_norm:
                exp1 = {
                    "recommended_action": "Proceed to catheterization lab immediately without systemic heparin anticoagulation",
                    "short_reason": "Managing active myocardial infarction takes precedence, but clinician directive requires holding heparin.",
                    "urgency": "critical",
                    "expected_effect": "PCI mechanical reperfusion bypasses thrombus load.",
                    "target_metric": "stability",
                    "action_type": "escalate"
                }
                exp2 = {
                    "recommended_action": "Hold heparin injection; ready bivalirudin or mechanical thrombectomy backups",
                    "short_reason": "Compliance with physician override to mitigate suspected major active bleeding hazards.",
                    "urgency": "high",
                    "expected_effect": "Avoid bleeding complications, but monitor closely for acute stent thrombosis.",
                    "target_metric": "pain_level",
                    "action_type": "supportive"
                }
                critic = {
                    "criticism": "Suspending all anticoagulation during acute anterior STEMI is a high-risk decision, but clinician override directs this to avoid severe bleeding. Recommend alternative procedural buffers.",
                    "suggested_modification": "Use mechanical aspiration catheters during the PCI to reduce clot load.",
                    "safety_flags": ["High risk of acute thrombosis"],
                    "confidence_score": 68,
                    "is_approved": False
                }
                orch = {
                    "recommended_action": "Activate cath lab for PCI without heparin per directive; ready mechanical thrombus filters",
                    "short_reason": "Clinician directed suspension of anticoagulation to mitigate bleeding hazard; proceeding with mechanical intervention.",
                    "urgency": "critical",
                    "expected_effect": "Coronary reperfusion under restricted anticoagulation status.",
                    "target_metric": "stability",
                    "action_type": "escalate"
                }
            elif "beta-blocker" in dir_norm:
                exp1 = {
                    "recommended_action": "Hold beta-blocker administration and re-evaluate rhythm stability",
                    "short_reason": "Beta-blockade is strictly contraindicated in cardiogenic shock or profound bradycardia.",
                    "urgency": "critical",
                    "expected_effect": "Prevent total circulatory collapse.",
                    "target_metric": "stability",
                    "action_type": "supportive"
                }
                exp2 = {
                    "recommended_action": "Ensure beta-blockers are completely held; verify intravenous pacing line is active",
                    "short_reason": "Beta-antagonism would further depress sinus node node function and cardiac output.",
                    "urgency": "critical",
                    "expected_effect": "Mitigate risk of complete heart block.",
                    "target_metric": "heart_rate",
                    "action_type": "supportive"
                }
                critic = {
                    "criticism": "Strict compliance with holding beta-blockers verified. Proceeding with active rate support.",
                    "suggested_modification": "Verify emergency transcutaneous pacemaker is in stand-by mode.",
                    "safety_flags": [],
                    "confidence_score": 95,
                    "is_approved": True
                }
                orch = {
                    "recommended_action": "Confirm beta-blockers are held; verify active pacing line backup",
                    "short_reason": "Clinician check confirmed potential cardiogenic shock hazard; keeping agents held.",
                    "urgency": "critical",
                    "expected_effect": "Maintain current sinus perfusion without drug-induced bradycardia exacerbation.",
                    "target_metric": "stability",
                    "action_type": "supportive"
                }
            else:
                # Custom directive fallback
                exp1 = {
                    "recommended_action": f"Incorporate directive: {directive}",
                    "short_reason": "Re-routing clinical decision based on custom clinician override.",
                    "urgency": "high",
                    "expected_effect": "Modify clinical outcomes to match operator guidance.",
                    "target_metric": "stability",
                    "action_type": "supportive"
                }
                exp2 = {
                    "recommended_action": f"Validate pharmacology for: {directive}",
                    "short_reason": "Analyze therapeutic boundaries of the override instructions.",
                    "urgency": "high",
                    "expected_effect": "Maintain safety constraints while aligning with commander inputs.",
                    "target_metric": "pain_level",
                    "action_type": "supportive"
                }
                critic = {
                    "criticism": f"Clinician directive '{directive}' reviewed. Safe boundaries applied.",
                    "suggested_modification": None,
                    "safety_flags": [],
                    "confidence_score": 85,
                    "is_approved": True
                }
                orch = {
                    "recommended_action": f"Execute override instruction: {directive}",
                    "short_reason": "Command directive prioritized over baseline protocol.",
                    "urgency": "high",
                    "expected_effect": "System state alignment with commander directives.",
                    "target_metric": "stability",
                    "action_type": "supportive"
                }
                
    elif d_lower == "disaster":
        if not directive:
            exp1 = {
                "recommended_action": "Deploy aerosolized alkaline water fog to neutralize chemical plume dispersion",
                "short_reason": "Suppresses vapor density and captures hydrochloric acid molecules in atmosphere.",
                "urgency": "critical",
                "expected_effect": "Reduce atmospheric ppm levels at downwind boundaries.",
                "target_metric": "hazmat_ppm",
                "action_type": "mitigate"
            }
            exp2 = {
                "recommended_action": "Evacuate Sector B primary school and establish a 1km exclusion barricade",
                "short_reason": "School lies directly in Eastern wind drift vector; must displace citizens prior to exposure.",
                "urgency": "critical",
                "expected_effect": "Prevent respiratory inhalation casualties in vulnerable groups.",
                "target_metric": "evacuation_percentage",
                "action_type": "escalate"
            }
            critic = {
                "criticism": "Water curtains are effective for HCl gas, but runoff must be diked to prevent sewer acid contamination. Evacuating Sector B school is critical and urgent.",
                "suggested_modification": "Notify fire crews to blockade storm drains to isolate acid runoff.",
                "safety_flags": [],
                "confidence_score": 90,
                "is_approved": True
            }
            orch = {
                "recommended_action": "Deploy vapor neutralization sprays and evacuate Sector B school immediately",
                "short_reason": "Chemical suppression halts hazard density, while evacuating downstream sectors prevents civilian casualties.",
                "urgency": "critical",
                "expected_effect": "Drop toxic gas concentration and raise evacuation levels.",
                "target_metric": "stability",
                "action_type": "mitigate"
            }
        else:
            exp1 = {
                "recommended_action": f"Alter deployment pattern to support: {directive}",
                "short_reason": "Commander directive injected into vapor containment strategy.",
                "urgency": "high",
                "expected_effect": "Adjust suppression boundaries.",
                "target_metric": "containment_rate",
                "action_type": "mitigate"
            }
            exp2 = {
                "recommended_action": f"Adjust evacuation routes to align: {directive}",
                "short_reason": "Clear exit paths according to command directions.",
                "urgency": "high",
                "expected_effect": "Restricted zone evacuation routing.",
                "target_metric": "evacuation_percentage",
                "action_type": "supportive"
            }
            critic = {
                "criticism": f"Incident commander directive '{directive}' reviewed. Runoff and wind vector checks completed.",
                "suggested_modification": None,
                "safety_flags": [],
                "confidence_score": 88,
                "is_approved": True
            }
            orch = {
                "recommended_action": f"Re-deploy containment units to execute: {directive}",
                "short_reason": "Command override directs containment positioning.",
                "urgency": "high",
                "expected_effect": "Contain hazard plume expansion per command directive.",
                "target_metric": "containment_rate",
                "action_type": "mitigate"
            }
            
    else:  # logistics
        if not directive:
            exp1 = {
                "recommended_action": "Re-route inbound container vessels to alternative Terminal Port B",
                "short_reason": "Offline crane systems block cargo unloading; Port B has open deepwater berths.",
                "urgency": "high",
                "expected_effect": "Bypass port network block and prevent anchorage demurrage accumulation.",
                "target_metric": "backlog_units",
                "action_type": "mitigate"
            }
            exp2 = {
                "recommended_action": "Establish secondary logistics motor carrier pools at backup dry depots",
                "short_reason": "Backup warehouse capacity is saturated; regional freight transfers require truck allocation.",
                "urgency": "high",
                "expected_effect": "Clear cargo backup from regional transfer docks.",
                "target_metric": "warehouse_capacity_percentage",
                "action_type": "supportive"
            }
            critic = {
                "criticism": "Routing ships to Port B bypasses terminal downtime, but custom checks could bottleneck if border agencies are not notified. Cargo pools must be balanced to avoid regional terminal lockups.",
                "suggested_modification": "Acquire pre-clearance certificates for diverted container vessels.",
                "safety_flags": [],
                "confidence_score": 85,
                "is_approved": True
            }
            orch = {
                "recommended_action": "Divert container vessels to Port B and mobilize secondary truck freight pools",
                "short_reason": "Alternative berthing restores deepwater offloading flow, backed by trucking pools to release hub saturation.",
                "urgency": "high",
                "expected_effect": "Decrease cargo backlogs and free backup hub space.",
                "target_metric": "backlog_units",
                "action_type": "mitigate"
            }
        else:
            exp1 = {
                "recommended_action": f"Adjust vessel schedules for: {directive}",
                "short_reason": "Logistics flow override requested by operations director.",
                "urgency": "high",
                "expected_effect": "Re-schedule transit lanes.",
                "target_metric": "routing_delay_hrs",
                "action_type": "mitigate"
            }
            exp2 = {
                "recommended_action": f"Optimize dry storage depots: {directive}",
                "short_reason": "Earmark warehouse sectors per directive.",
                "urgency": "high",
                "expected_effect": "Restore supply chains.",
                "target_metric": "warehouse_capacity_percentage",
                "action_type": "supportive"
            }
            critic = {
                "criticism": f"Operations override '{directive}' verified. Customs and carrier bottlenecks mapped.",
                "suggested_modification": None,
                "safety_flags": [],
                "confidence_score": 82,
                "is_approved": True
            }
            orch = {
                "recommended_action": f"Authorize emergency logistics diversion: {directive}",
                "short_reason": "Consolidating transit routing to reflect director directives.",
                "urgency": "high",
                "expected_effect": "Unblock shipping corridor bottlenecks.",
                "target_metric": "backlog_units",
                "action_type": "mitigate"
            }
            
    return exp1, exp2, critic, orch

# ----------------- Core Workflow Graph Pipeline -----------------
class WorkflowGraphEngine:
    """Executes AegisFlow's layered multi-agent operational simulation pipeline."""

    @staticmethod
    async def execute_step(
        session_id: str,
        domain: str,
        state: SimulationState,
        active_directive: Optional[str] = None
    ) -> SessionSnapshot:
        """Run the complete asynchronous multi-agent simulation graph."""
        
        # Track steps execution metadata
        steps: List[ExecutionStep] = []
        
        def log_step(name: str, status: str, summary: Optional[str] = None, dur: Optional[float] = None):
            steps.append(ExecutionStep(
                node_name=name,
                status=status,
                output_summary=summary,
                timestamp=datetime.now(timezone.utc),
                duration_ms=dur
            ))

        # --- NODE 1: CONTEXT PREP ---
        t_start = time.perf_counter()
        domain_cfg = DOMAIN_AGENTS.get(domain.lower())
        if not domain_cfg:
            raise ValueError(f"Unknown domain: {domain}")
            
        case_summary = f"DOMAIN: {domain}\nSTATE SUMMARY: {state.status_summary}\nSTABILITY: {state.stability_score}\nRISK: {state.risk_level}\nMETRICS: {state.metrics}\nPENDING ACTIONS: {state.pending_actions}"
        if active_directive:
            case_summary += f"\nHUMAN OPERATOR OVERRIDE DIRECTIVE:\n{active_directive}"
            
        duration = (time.perf_counter() - t_start) * 1000.0
        log_step("CONTEXT_PREP", "completed", "Simulation context serialized.", duration)
        
        # API check
        api_available = _get_genai_client() is not None
        
        exp1_prop = None
        exp2_prop = None
        critic_rep = None
        orch_prop = None
        
        if api_available:
            try:
                # --- NODE 2: PARALLEL PROPOSAL GENERATION ---
                t_start = time.perf_counter()
                
                # Prompts building
                p1_prompt = (
                    f"You are the {domain_cfg['expert_1']['role']}.\n"
                    f"Goal: {domain_cfg['expert_1']['goal']}\n"
                    f"Backstory: {domain_cfg['expert_1']['backstory']}\n\n"
                    f"Current Simulation State Snapshot:\n{case_summary}\n\n"
                    "Output your recommendation in precisely this format:\n"
                    "Recommended Action: <one sentence>\n"
                    "Short Reason: <one sentence>\n"
                    "Urgency: <critical|high|moderate|low>\n"
                    "Expected Effect: <short description>\n"
                    "Target Metric: <name of the metric affected>\n"
                    "Action Type: <escalate|mitigate|rhythm_support|unsafe|supportive|monitor>\n"
                )
                
                p2_prompt = (
                    f"You are the {domain_cfg['expert_2']['role']}.\n"
                    f"Goal: {domain_cfg['expert_2']['goal']}\n"
                    f"Backstory: {domain_cfg['expert_2']['backstory']}\n\n"
                    f"Current Simulation State Snapshot:\n{case_summary}\n\n"
                    "Output your recommendation in precisely this format:\n"
                    "Recommended Action: <one sentence>\n"
                    "Short Reason: <one sentence>\n"
                    "Urgency: <critical|high|moderate|low>\n"
                    "Expected Effect: <short description>\n"
                    "Target Metric: <name of the metric affected>\n"
                    "Action Type: <escalate|mitigate|rhythm_support|unsafe|supportive|monitor>\n"
                )
                
                # Run in parallel using asyncio threadpool wrapper
                loop = asyncio.get_running_loop()
                task1 = loop.run_in_executor(None, _call_gemini_api, p1_prompt, 0.2)
                task2 = loop.run_in_executor(None, _call_gemini_api, p2_prompt, 0.2)
                
                res1, res2 = await asyncio.gather(task1, task2)
                
                parsed1 = _parse_proposal_response(res1)
                parsed2 = _parse_proposal_response(res2)
                
                exp1_prop = AgentProposal(**parsed1)
                exp2_prop = AgentProposal(**parsed2)
                
                duration = (time.perf_counter() - t_start) * 1000.0
                log_step("PROPOSAL_GENERATION", "completed", f"Parallel proposals generated by {domain_cfg['expert_1']['role']} and {domain_cfg['expert_2']['role']}.", duration)
                
                # --- NODE 3: CRITIC SAFETY REVIEW ---
                t_start = time.perf_counter()
                
                critic_prompt = (
                    f"You are the {domain_cfg['critic']['role']}.\n"
                    f"Goal: {domain_cfg['critic']['goal']}\n"
                    f"Backstory: {domain_cfg['critic']['backstory']}\n\n"
                    f"Simulation Context:\n{case_summary}\n\n"
                    f"Specialist Proposal 1 ({domain_cfg['expert_1']['role']}):\n{json.dumps(parsed1, indent=2)}\n\n"
                    f"Specialist Proposal 2 ({domain_cfg['expert_2']['role']}):\n{json.dumps(parsed2, indent=2)}\n\n"
                    "Assess these recommendations for risks, conflicts, toxic boundaries, or danger. Format your critique exactly as:\n"
                    "Criticism: <detailed explanation>\n"
                    "Suggested Modification: <modification suggestions>\n"
                    "Safety Flags: <comma-separated list of flags, or None>\n"
                    "Confidence Score: <number between 0 and 100>\n"
                )
                
                critic_res = await loop.run_in_executor(None, _call_gemini_api, critic_prompt, 0.1)
                critic_parsed = _parse_review_response(critic_res)
                critic_rep = ReviewReport(**critic_parsed)
                
                duration = (time.perf_counter() - t_start) * 1000.0
                log_step("CRITIC_REVIEW", "completed", f"Critic review executed. Score: {critic_rep.confidence_score}. Safety Flags: {len(critic_rep.safety_flags)}", duration)
                
                # --- NODE 4: CONFLICT RESOLUTION / ORCHESTRATOR ---
                t_start = time.perf_counter()
                
                orch_prompt = (
                    f"You are the {domain_cfg['orchestrator']['role']}.\n"
                    f"Goal: {domain_cfg['orchestrator']['goal']}\n"
                    f"Backstory: {domain_cfg['orchestrator']['backstory']}\n\n"
                    f"Context:\n{case_summary}\n\n"
                    f"Proposal 1 ({domain_cfg['expert_1']['role']}):\n{json.dumps(parsed1, indent=2)}\n\n"
                    f"Proposal 2 ({domain_cfg['expert_2']['role']}):\n{json.dumps(parsed2, indent=2)}\n\n"
                    f"Critic Review:\n{json.dumps(critic_parsed, indent=2)}\n\n"
                    "Reconcile conflicts, integrate critic guidelines, and finalize the command action. Format exactly as:\n"
                    "Recommended Action: <one sentence resolved command>\n"
                    "Short Reason: <one sentence resolution rationale>\n"
                    "Urgency: <critical|high|moderate|low>\n"
                    "Expected Effect: <short description>\n"
                    "Target Metric: <target metric name>\n"
                    "Action Type: <escalate|mitigate|rhythm_support|unsafe|supportive|monitor>\n"
                )
                
                orch_res = await loop.run_in_executor(None, _call_gemini_api, orch_prompt, 0.2)
                orch_parsed = _parse_proposal_response(orch_res)
                orch_prop = AgentProposal(**orch_parsed)
                
                duration = (time.perf_counter() - t_start) * 1000.0
                log_step("RESOLVE_CONSENSUS", "completed", "Orchestrator resolved final command.", duration)
                
            except Exception as e:
                # API Call error: log and fall back to sandbox generators
                log_step("API_EXECUTION", "failed", f"Gemini API failure: {e}. Falling back to simulation engine.")
                api_available = False
                
        if not api_available:
            # Run high-fidelity simulator mode
            t_start = time.perf_counter()
            # Simulate processing delay for aesthetics
            await asyncio.sleep(0.6)
            
            p1_m, p2_m, critic_m, orch_m = _get_sandbox_fallback(domain, active_directive)
            
            exp1_prop = AgentProposal(**p1_m)
            exp2_prop = AgentProposal(**p2_m)
            
            log_step("PROPOSAL_GENERATION", "completed", f"Parallel proposals generated by {domain_cfg['expert_1']['role']} and {domain_cfg['expert_2']['role']} (Simulated).", 300)
            
            critic_rep = ReviewReport(**critic_m)
            log_step("CRITIC_REVIEW", "completed", f"Critic review executed. Score: {critic_rep.confidence_score}. Safety Flags: {len(critic_rep.safety_flags)} (Simulated).", 150)
            
            orch_prop = AgentProposal(**orch_m)
            log_step("RESOLVE_CONSENSUS", "completed", "Orchestrator resolved final command (Simulated).", 150)
            
        # --- NODE 5: STATE ENGINE UPDATE ---
        t_start = time.perf_counter()
        
        # Apply the final orchestrator decision to the state
        outcome_res = apply_proposal_transition(orch_prop, state)
        # Sync effect label
        orch_prop.effect_label = outcome_res["effect_label"]
        
        # Calculate evaluation score
        eval_profile = generate_confidence_profile(
            [exp1_prop, exp2_prop], 
            critic_rep, 
            active_directive is not None
        )
        
        duration = (time.perf_counter() - t_start) * 1000.0
        log_step("STATE_MUTATION", "completed", f"Simulation rules applied. Outcome: {state.state_outcome}. Reliability: {eval_profile['final_reliability_score']}%", duration)
        
        # --- NODE 6: COMMIT LOGS & EVENTS ---
        t_start = time.perf_counter()
        
        # Formulate Events to append to the transcript
        event_prefix = "revised" if active_directive else "proposed"
        
        # 1. Specialist 1
        e1 = EventSchema(
            id=f"evt_{domain.lower()}_exp1_{datetime.now(timezone.utc).timestamp()}",
            role="expert_1",
            display_name=domain_cfg["expert_1"]["role"],
            event_type="proposal",
            status=event_prefix,
            content=f"**Recommended Action**: {exp1_prop.recommended_action}\n\n**Reasoning**: {exp1_prop.short_reason}\n* Urgency: {exp1_prop.urgency.upper()} | Expected Effect: {exp1_prop.expected_effect or 'N/A'}",
            action_metadata=exp1_prop
        )
        
        # 2. Specialist 2
        e2 = EventSchema(
            id=f"evt_{domain.lower()}_exp2_{datetime.now(timezone.utc).timestamp()}",
            role="expert_2",
            display_name=domain_cfg["expert_2"]["role"],
            event_type="proposal",
            status=event_prefix,
            content=f"**Recommended Action**: {exp2_prop.recommended_action}\n\n**Reasoning**: {exp2_prop.short_reason}\n* Urgency: {exp2_prop.urgency.upper()} | Expected Effect: {exp2_prop.expected_effect or 'N/A'}",
            action_metadata=exp2_prop
        )
        
        # 3. Critic Check
        flags_info = f"\n* **Safety Warnings Triggered**: {', '.join(critic_rep.safety_flags)}" if critic_rep.safety_flags else "\n* **Safety Warnings**: None detected"
        e_critic = EventSchema(
            id=f"evt_{domain.lower()}_critic_{datetime.now(timezone.utc).timestamp()}",
            role="critic",
            display_name=domain_cfg["critic"]["role"],
            event_type="review",
            status=event_prefix,
            content=f"**Audited Evaluation**: {critic_rep.criticism}\n\n* **Confidence Rating**: {critic_rep.confidence_score}/100\n* **Suggested Modification**: {critic_rep.suggested_modification or 'None'}{flags_info}",
            review_metadata=critic_rep
        )
        
        # 4. Orchestrator finalized
        e_orch = EventSchema(
            id=f"evt_{domain.lower()}_orch_{datetime.now(timezone.utc).timestamp()}",
            role="orchestrator",
            display_name=domain_cfg["orchestrator"]["role"],
            event_type="orchestration",
            status="final",
            content=f"**Resolved Command**: {orch_prop.recommended_action}\n\n**Consensus Summary**: {orch_prop.short_reason}",
            action_metadata=orch_prop,
            state_change_summary=state.latest_change
        )
        
        # Attach execution trace steps to system commits
        log_step("COMMIT_LOGS", "completed", "Session snapshots finalized.")
        
        e_sys = EventSchema(
            id=f"evt_sys_{datetime.now(timezone.utc).timestamp()}",
            role="system",
            display_name="Simulation Pipeline",
            event_type="system_event",
            status="final",
            content=f"AegisFlow pipeline successfully processed operational cycle in {sum([s.duration_ms for s in steps if s.duration_ms]) or 800:.1f}ms.",
            state_change_summary=state.latest_change,
            execution_steps=steps
        )
        
        # Construct snapshot
        scenario = SCENARIOS.get(domain.lower())
        snapshot = SessionSnapshot(
            session_id=session_id,
            domain=domain,
            scenario_name=scenario["scenario_name"],
            case_data=scenario["case_data"],
            events=[e1, e2, e_critic, e_orch, e_sys], # Returned for this cycle
            active_directive=active_directive,
            safety_flags=eval_profile["flags_triggered"],
            next_action=state.pending_actions[0] if state.pending_actions else "Monitor general conditions",
            simulation_state=state
        )
        
        return snapshot
