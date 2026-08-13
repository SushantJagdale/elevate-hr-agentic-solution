"""Integration tests for all 6 MVP Use Cases defined in Consolidated SDD."""

import unittest
from app.agent.orchestrator import hr_orchestrator
from app.services.workweek_service import workweek_db
from app.services.service_immediately_service import servicenow_db
from app.services.policy_knowledge_service import policy_service


class TestUseCases(unittest.TestCase):

    def test_uc_1_1_policy_qa_bereavement(self):
        """UC-1.1: Verify grounded policy Q&A for bereavement leave."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc1_1",
            user_prompt="What is the company's bereavement leave policy in Singapore?",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("bereavement", turn_res["response"].lower())
        self.assertTrue(len(turn_res["citations"]) > 0 or "leave" in turn_res["response"].lower())

    def test_uc_1_1_policy_qa_refusal_for_unrelated(self):
        """UC-1.1: Verify deterministic refusal when policy does not contain information."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc1_1_refusal",
            user_prompt="Can I bring my pet iguana to the Singapore office according to policy?",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertTrue(
            "official policy records do not contain sufficient information" in turn_res["response"]
            or "refusal" in str(turn_res).lower()
        )

    def test_uc_1_2_hr_self_service_balances(self):
        """UC-1.2: Check accrued and remaining leave balances."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc1_2_bal",
            user_prompt="How many vacation days and sick leave balance do I have left?",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("Vacation", turn_res["response"])
        self.assertIn("Sick Leave", turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "get_leave_balances" for t in turn_res["tool_calls"]))

    def test_uc_1_2_submit_leave(self):
        """UC-1.2: Submit a valid leave request in WorkWeek."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc1_2_sub",
            user_prompt="Please submit a vacation request for next week.",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("Submitted", turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "submit_leave_request" for t in turn_res["tool_calls"]))

    def test_uc_1_3_incident_creation(self):
        """UC-1.3: Create IT incident support ticket."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc1_3_inc",
            user_prompt="Create an IT ticket because my VPN connection keeps dropping repeatedly.",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("INC00", turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "create_support_ticket" for t in turn_res["tool_calls"]))

    def test_uc_2_1_equipment_procurement(self):
        """UC-2.1: Cross-system hardware procurement (Policy -> Profile check -> Hardware order)."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc2_1_equip",
            user_prompt="I am a remote engineer. Please check my eligibility and order a 27-inch 4K monitor.",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("REQ00", turn_res["response"])
        self.assertIn("Monitor", turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "order_hardware_equipment" for t in turn_res["tool_calls"]))

    def test_uc_2_2_medical_leave_with_it_routing(self):
        """UC-2.2: Cross-system medical leave filing and IT routing ticket."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc2_2_med",
            user_prompt="I need to file 5 days of medical leave for hospital surgery.",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertIn("LV-", turn_res["response"])
        self.assertIn("INC00", turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "file_medical_leave_with_it_routing" for t in turn_res["tool_calls"]))

    def test_uc_2_3_relocation_support(self):
        """UC-2.3: Cross-system relocation (Address update in HCM + Facilities ticket)."""
        turn_res = hr_orchestrator.run_turn(
            session_id="test_uc2_3_reloc",
            user_prompt="I am relocating to Singapore. Please update my home address and request office badge access.",
        )
        self.assertEqual(turn_res["status"], "success")
        self.assertTrue("Address updated" in turn_res["response"] or "Relocation" in turn_res["response"])
        self.assertTrue(any(t["tool_name"] == "process_relocation_request" for t in turn_res["tool_calls"]))


if __name__ == "__main__":
    unittest.main()
