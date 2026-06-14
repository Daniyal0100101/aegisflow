from typing import Any, Dict

# Baseline simulation scenarios database
SCENARIOS: Dict[str, Dict[str, Any]] = {
    "clinical": {
        "scenario_name": "Clinical Emergency: Acute STEMI Coordinator",
        "case_data": {
            "patient_name": "James Doe",
            "age": 68,
            "sex": "M",
            "diagnosis_summary": "Acute anterior STEMI with bradycardia and hypotension",
            "admission_timing": "Admitted 20m ago",
            "ef": "30%",
            "bp": "86/54",
            "hr": "38",
            "oxygen_saturation": 89,
            "pain_level": 8,
        },
        "initial_state": {
            "status_summary": "Unstable STEMI with ongoing chest pain and poor perfusion",
            "stability_score": 32,
            "risk_level": "critical",
            "metrics": {
                "heart_rate": 38,
                "blood_pressure": "86/54",
                "oxygen_saturation": 89,
                "pain_level": 8,
                "ejection_fraction": "30%",
            },
            "interventions_done": [],
            "decisions_applied": [],
            "pending_actions": [
                "Urgent reperfusion decision",
                "Continuous cardiac monitoring",
                "Medication safety review"
            ],
            "latest_change": "Simulation initialized from STEMI case.",
            "state_outcome": "Unchanged",
            "timeline": ["Baseline state: unstable clinical STEMI case loaded."]
        }
    },
    "disaster": {
        "scenario_name": "Disaster Response: Industrial Toxic Vapor Leak",
        "case_data": {
            "incident_name": "Operation Plume Containment",
            "facility_name": "Apex Chemical Depot",
            "coordinates": "Grid Sector 4A (Industrial)",
            "incident_timing": "Detonation +35m",
            "plume_gas": "Hydrogen Chloride",
            "wind_speed": "18 mph (East)",
            "leak_rate": "85 kg/min",
            "affected_population": "approx 12,000",
        },
        "initial_state": {
            "status_summary": "Toxic HCl gas dispersing east toward residential Zone B. Plume expanding rapidly.",
            "stability_score": 25,
            "risk_level": "critical",
            "metrics": {
                "containment_rate": 15,          # % containment
                "hazmat_ppm": 420,                 # ppm in zone B boundary
                "evacuation_percentage": 12,       # % evacuated
                "injured_count": 6,                # count
                "wind_speed_mph": 18,
            },
            "interventions_done": [],
            "decisions_applied": [],
            "pending_actions": [
                "Deploy aerosol neutralizer fog",
                "Establish perimeter blockade",
                "Evacuate Sector B elementary school"
            ],
            "latest_change": "Simulation initialized from Class 3 vapor rupture.",
            "state_outcome": "Unchanged",
            "timeline": ["Baseline state: hazardous chemical release containment initiated."]
        }
    },
    "logistics": {
        "scenario_name": "Logistics Recovery: Maritime Port Cyber Outage",
        "case_data": {
            "port_name": "Gateway Terminals East",
            "terminal_status": "LOCKED (Ransomware)",
            "idle_vessels": 9,
            "backlog_value": "$12.4M",
            "active_routing_delay": "14 hrs",
            "cargo_type": "Refrigerated and Auto-parts",
            "backup_hub_capacity": "Secondary depot at 94% capacity",
        },
        "initial_state": {
            "status_summary": "Cargo terminal OS and crane controls offline. 9 vessels idle at anchor. Rail hubs backed up.",
            "stability_score": 35,
            "risk_level": "high",
            "metrics": {
                "backlog_units": 2200,            # containers delayed
                "routing_delay_hrs": 14,           # average route delay
                "warehouse_capacity_percentage": 96, # backup hub saturation
                "idle_vessels": 9,
                "active_sla_violations": 45,
            },
            "interventions_done": [],
            "decisions_applied": [],
            "pending_actions": [
                "Re-route incoming vessels to Port B",
                "Initiate secondary truck carrier pooling",
                "Audit regional warehouse storage capacity caps"
            ],
            "latest_change": "Simulation initialized from terminal network lockout.",
            "state_outcome": "Unchanged",
            "timeline": ["Baseline state: supply chain network terminal failure active."]
        }
    }
}

# Specialist, Critic, and Orchestrator Profiles per domain
DOMAIN_AGENTS: Dict[str, Dict[str, Any]] = {
    "clinical": {
        "expert_1": {
            "role": "Lead Cardiologist",
            "goal": "Recommend hemodynamic stabilization and cardiac reperfusion strategies.",
            "backstory": "An experienced emergency interventional cardiologist with deep expertise in acute STEMI management and catheterization procedures. You provide rapid, decisive, clinically-sound recommendations. Never defer decisions, and never ask for more diagnostics."
        },
        "expert_2": {
            "role": "Clinical Pharmacist",
            "goal": "Provide medication safety guidance, dosage constraints, and thrombolytic checklists.",
            "backstory": "A specialized critical care pharmacist with expertise in emergency cardiovascular pharmacology. You inspect drug-drug interactions, analyze medication contraindications (e.g. bleeding risk during anticoagulation), and recommend precise infusion regimens."
        },
        "critic": {
            "role": "Clinical Safety Critic",
            "goal": "Analyze specialist recommendations for clinical contraindications, safety hazards, and risk levels.",
            "backstory": "A senior medical safety director responsible for quality assurance in clinical pathways. You review proposals with high skepticism, checking for conflicts, toxic dosages, or dangerous procedural delays. You issue safety flags and confidence ratings."
        },
        "orchestrator": {
            "role": "Clinical Consensus Director",
            "goal": "Synthesize specialist proposals and critic evaluations to produce a single resolved action.",
            "backstory": "A seasoned Chief of Emergency Medicine. You resolve disagreements between the cardiologist and pharmacist, apply the safety critic's corrections, and synthesize a single, clear, actionable decision that prioritizes patient survival and systemic safety."
        }
    },
    "disaster": {
        "expert_1": {
            "role": "Hazmat Response Engineer",
            "goal": "Design toxic vapor suppression, chemical neutralization, and barrier containment plans.",
            "backstory": "An industrial hazard safety veteran. You calculate chemical dispersion plumes, select appropriate neutralization agents (e.g., water curtains, weak alkaline spray for HCl), and prioritize halting the source leak."
        },
        "expert_2": {
            "role": "Public Safety Evacuation Captain",
            "goal": "Plan perimeter blockades, evacuation corridors, and shelter-in-place zoning.",
            "backstory": "A veteran emergency operations commander. You coordinate neighborhood clearing, traffic control blockages, triage depot setup, and prioritize vulnerable zones (schools, hospitals) based on plume trajectory."
        },
        "critic": {
            "role": "Emergency Response Safety Auditor",
            "goal": "Evaluate disaster response plans for responder toxic exposure limits and civilian entrapment risks.",
            "backstory": "A federal emergency inspector. You verify if responders have proper protective gear, if water spray will cause toxic runoffs, and if evacuation directions route civilians directly into the toxic path. You highlight fatal flaws."
        },
        "orchestrator": {
            "role": "Emergency Incident Commander",
            "goal": "Consolidate containment and evacuation proposals into a unified, risk-mitigated crisis action plan.",
            "backstory": "A city emergency management director. You synthesize hazmat containment with civilian evacuation logistics, resolve resource competition, apply auditor precautions, and issue clear incident directives."
        }
    },
    "logistics": {
        "expert_1": {
            "role": "Global Route Coordinator",
            "goal": "Re-route ocean carriers, schedule backup rail networks, and coordinate secondary ports.",
            "backstory": "A maritime shipping analyst. You redirect ships at anchor, negotiate terminal berths at alternative ports, and coordinate multimodal rail and container truck logistics."
        },
        "expert_2": {
            "role": "Regional Inventory Planner",
            "goal": "Manage warehouse capacity overflows, optimize priority shipments, and release safety stock buffers.",
            "backstory": "An enterprise supply chain planner. You track shelf life, manage storage volume overflows, establish auto-allocation quotas for critical auto parts or medical goods, and coordinate dry storage transfers."
        },
        "critic": {
            "role": "Supply Chain Risk Critic",
            "goal": "Analyze re-routing and inventory plans for customs clearance delays and warehouse bottlenecks.",
            "backstory": "A commercial supply chain auditor. You audit proposals for demurrage charges, warehouse labor capacity caps, and critical customs inspection delays. You warn about plans that shift bottlenecks rather than solve them."
        },
        "orchestrator": {
            "role": "Operations Recovery Director",
            "goal": "Resolve routing and storage conflicts to generate a single logistics response that preserves delivery SLAs.",
            "backstory": "A Chief Supply Chain Operations Officer. You weigh route costs against delivery delays, allocate critical warehouse space, clear legal hurdles highlighted by the auditor, and finalize the system recovery plan."
        }
    }
}
