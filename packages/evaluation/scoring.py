from typing import Any, Dict, List
from packages.shared_types.models import AgentProposal, ReviewReport

def generate_confidence_profile(
    proposals: List[AgentProposal], 
    review: ReviewReport, 
    active_directive: bool
) -> Dict[str, Any]:
    """Calculate structured confidence ratings and safety audit trail metrics."""
    
    # Calculate specialist alignment coefficient
    action_types = [p.action_type for p in proposals]
    unique_types = set(action_types)
    
    if len(proposals) <= 1:
        alignment_score = 1.0
    elif len(unique_types) == 1:
        alignment_score = 1.0
    else:
        # If specialists differ, lower alignment coefficient
        alignment_score = max(0.2, 1.0 - (len(unique_types) / len(proposals)))
        
    # Scale based on review confidence
    base_confidence = review.confidence_score
    
    # Human override adjustments
    human_alignment_bonus = 15 if active_directive else 0
    
    # Safety flag penalties
    safety_penalty = len(review.safety_flags) * 20
    
    final_score = int(max(5, min(100, (base_confidence * alignment_score) + human_alignment_bonus - safety_penalty)))
    
    # Risk assessment mapping
    if final_score >= 80:
        safety_grade = "A (Optimal)"
        risk_level = "Low"
    elif final_score >= 60:
        safety_grade = "B (Qualified)"
        risk_level = "Moderate"
    elif final_score >= 40:
        safety_grade = "C (Sub-optimal)"
        risk_level = "High"
    else:
        safety_grade = "D (Risk-Imminent)"
        risk_level = "Critical"
        
    return {
        "final_reliability_score": final_score,
        "specialist_alignment_coefficient": round(alignment_score, 2),
        "safety_audit_grade": safety_grade,
        "calculated_risk_level": risk_level,
        "active_warnings": len(review.safety_flags),
        "flags_triggered": review.safety_flags,
    }
