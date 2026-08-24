import unittest

from main import AgentSpec, ControlPlane, RuntimeSignals, authorize_tool, evaluate_rollout


class ControlPlaneTests(unittest.TestCase):
    def test_unregistered_tool_is_denied(self):
        spec = AgentSpec("agent", ["search"], max_cost=.25)
        self.assertEqual(authorize_tool(spec, "refund")["decision"], "DENY")

    def test_approval_tool_requires_review(self):
        spec = AgentSpec("agent", ["refund"], max_cost=.25, requires_approval=["refund"])
        self.assertEqual(authorize_tool(spec, "refund")["decision"], "REVIEW")
        self.assertEqual(authorize_tool(spec, "refund", approved=True)["decision"], "ALLOW")

    def test_failed_gate_holds_rollout(self):
        spec = AgentSpec("agent", [], max_cost=.25, min_eval=.85, rollout="canary")
        result = evaluate_rollout(spec, .70, .001, .10)
        self.assertEqual(result["state"], "HOLD")
        self.assertIn("eval-below-gate", result["blockers"])

    def test_audit_records_decisions(self):
        plane = ControlPlane()
        spec = AgentSpec("agent", ["search"], max_cost=.25, rollout="shadow")
        plane.register(spec)
        plane.authorize("agent", "search")
        plane.assess("agent", RuntimeSignals(.9, .001, .1))
        self.assertEqual(len(plane.audit), 3)
        self.assertEqual(plane.audit[-1]["event"], "rollout-assessment")


if __name__ == "__main__":
    unittest.main()
