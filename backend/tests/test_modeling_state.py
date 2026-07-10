import unittest

from services.modeling_state import WorkflowTransitionError, next_state, previous_state


class ModelingStateTests(unittest.TestCase):
    def test_advances_only_to_declared_successor(self):
        self.assertEqual(next_state("project_initialized"), "problem_parsing")
        self.assertEqual(next_state("model_approval_pending"), "experiment_implementation")

    def test_completed_project_cannot_advance(self):
        with self.assertRaises(WorkflowTransitionError):
            next_state("completed")

    def test_rollback_uses_declared_editable_predecessor(self):
        self.assertEqual(previous_state("model_approval_pending"), "model_planning")
        self.assertEqual(previous_state("execution_approval_pending"), "experiment_implementation")

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(WorkflowTransitionError):
            next_state("made_up")
