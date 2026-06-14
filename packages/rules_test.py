import unittest
from packages.shared_types.models import SimulationState, AgentProposal, ReviewReport
from packages.state_engine.rules import apply_proposal_transition
from packages.evaluation.scoring import generate_confidence_profile

class TestAegisFlowEngine(unittest.TestCase):
    
    def setUp(self):
        # Baseline Clinical State
        self.clinical_state = SimulationState(
            domain="clinical",
            scenario_id="clinical",
            status_summary="Baseline clinical scenario",
            stability_score=32,
            risk_level="critical",
            metrics={
                "heart_rate": 38,
                "blood_pressure": "86/54",
                "oxygen_saturation": 89,
                "pain_level": 8,
            },
            interventions_done=[],
            decisions_applied=[],
            pending_actions=["Urgent reperfusion decision"],
            latest_change="Initial",
            state_outcome="Unchanged",
            timeline=[]
        )

        # Baseline Disaster State
        self.disaster_state = SimulationState(
            domain="disaster",
            scenario_id="disaster",
            status_summary="Baseline disaster scenario",
            stability_score=25,
            risk_level="critical",
            metrics={
                "containment_rate": 15,
                "hazmat_ppm": 420,
                "evacuation_percentage": 12,
                "injured_count": 6
            },
            interventions_done=[],
            decisions_applied=[],
            pending_actions=["Deploy neutralizer"],
            latest_change="Initial",
            state_outcome="Unchanged",
            timeline=[]
        )

    def test_clinical_escalate_improves_state(self):
        proposal = AgentProposal(
            recommended_action="Activate cath lab",
            short_reason="Urgent coronary reperfusion is required.",
            urgency="critical",
            target_metric="stability",
            action_type="escalate"
        )
        
        res = apply_proposal_transition(proposal, self.clinical_state)
        self.assertEqual(res["state_outcome"], "Improved")
        self.assertEqual(res["effect_label"], "improving")
        self.assertGreater(self.clinical_state.stability_score, 32)
        self.assertEqual(self.clinical_state.metrics["oxygen_saturation"], 91)
        self.assertEqual(self.clinical_state.metrics["pain_level"], 6)

    def test_clinical_unsafe_worsens_state(self):
        proposal = AgentProposal(
            recommended_action="Administer high dose beta blocker check",
            short_reason="Trialing beta blocker.",
            urgency="critical",
            target_metric="heart_rate",
            action_type="unsafe"
        )
        
        res = apply_proposal_transition(proposal, self.clinical_state)
        self.assertEqual(res["state_outcome"], "Worsened")
        self.assertEqual(res["effect_label"], "worsening")
        self.assertLess(self.clinical_state.stability_score, 32)
        self.assertEqual(self.clinical_state.metrics["heart_rate"], 34)

    def test_disaster_neutralizer_mitigates_hazard(self):
        proposal = AgentProposal(
            recommended_action="Deploy aerosol water fog curtains",
            short_reason="Halts toxic HCI expansion.",
            urgency="critical",
            target_metric="containment_rate",
            action_type="mitigate"
        )
        
        res = apply_proposal_transition(proposal, self.disaster_state)
        self.assertEqual(res["state_outcome"], "Improved")
        self.assertEqual(self.disaster_state.metrics["containment_rate"], 35)
        self.assertEqual(self.disaster_state.metrics["hazmat_ppm"], 340)

    def test_evaluation_scoring(self):
        proposal1 = AgentProposal(
            recommended_action="Action A", short_reason="R1", urgency="critical", target_metric="m1", action_type="mitigate"
        )
        proposal2 = AgentProposal(
            recommended_action="Action B", short_reason="R2", urgency="critical", target_metric="m2", action_type="mitigate"
        )
        review = ReviewReport(
            safety_flags=[],
            confidence_score=90,
            criticism="Excellent plan alignment",
            is_approved=True
        )
        
        score_profile = generate_confidence_profile([proposal1, proposal2], review, active_directive=False)
        self.assertEqual(score_profile["final_reliability_score"], 90) # 90 * 1.0 = 90
        self.assertEqual(score_profile["safety_audit_grade"], "A (Optimal)")

        # Adding warnings reduces score
        review_with_flags = ReviewReport(
            safety_flags=["Exposure limit warning"],
            confidence_score=80,
            criticism="Warning active",
            is_approved=False
        )
        score_profile_flags = generate_confidence_profile([proposal1, proposal2], review_with_flags, active_directive=False)
        self.assertLess(score_profile_flags["final_reliability_score"], 80)

if __name__ == "__main__":
    unittest.main()
