from django.test import TestCase
import asyncio
import sys
import os
import time

# Import State Machine & Multi-Agent Graph components from manage.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from manage import (
    execute_async_agent_graph,
    AsyncAgentGraphStateMachine,
    AgentGraphState,
    GraphStatus,
    StateSchema,
)


class AsyncAgentGraphStateMachineTest(TestCase):
    """Comprehensive test suite for Asynchronous Multi-Agent Graph State Machine with Fallback Routing."""

    def test_successful_graph_execution(self):
        """Verify normal single-path graph execution without errors."""
        input_data = {
            "invoice_id": "INV-1001",
            "vendor": "TechSupplies Corp",
            "total_amount": 499.99,
            "confidence_score": 0.98,
        }
        state = execute_async_agent_graph(input_data)
        
        self.assertEqual(state.status, GraphStatus.SUCCESS)
        self.assertFalse(state.fallback_triggered)
        self.assertEqual(len(state.errors), 0)
        self.assertEqual(state.extracted_data.get("invoice_id"), "INV-1001")
        self.assertEqual(state.extracted_data.get("extraction_method"), "Primary_LLM_Node")
        self.assertIn("_metadata", state.extracted_data)

    def test_retry_edge_traversal_with_exponential_backoff(self):
        """Verify transient primary extractor node failure triggers retry edge with exponential backoff."""
        attempt_count = 0

        def FlakyExtractor(input_payload):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                raise RuntimeError(f"Transient LLM timeout on attempt {attempt_count}")
            return {
                "invoice_id": "INV-RETRY-SUCCESS",
                "vendor": "Flaky Vendor",
                "total_amount": 250.0,
                "confidence_score": 0.92,
                "extraction_method": "Primary_LLM_Node_FlakyRecovered",
            }

        start_time = time.time()
        state = execute_async_agent_graph(
            input_data={"test": "flaky"},
            max_retries=3,
            initial_delay=0.02,
            backoff_factor=2.0,
            primary_extractor_fn=FlakyExtractor,
        )
        elapsed = time.time() - start_time

        self.assertEqual(state.status, GraphStatus.SUCCESS)
        self.assertFalse(state.fallback_triggered)
        self.assertEqual(state.retry_counts.get("PRIMARY_EXTRACTOR"), 2)
        self.assertEqual(len(state.errors), 2)
        # Verify backoff delays were applied (0.02 + 0.04 = 0.06s minimum)
        self.assertGreaterEqual(elapsed, 0.05)
        self.assertEqual(state.extracted_data.get("invoice_id"), "INV-RETRY-SUCCESS")

    def test_fallback_routing_on_max_retries_exceeded(self):
        """Verify persistent primary failure triggers FallbackExtractorNode recovery path without pipeline termination."""
        def AlwaysFailingExtractor(input_payload):
            raise RuntimeError("Persistent LLM API rate limit exceeded")

        def CustomFallbackExtractor(input_payload):
            return {
                "invoice_id": "INV-FALLBACK-RECOVERED",
                "vendor": "Fallback Parser",
                "total_amount": 100.0,
                "confidence_score": 0.50,
                "extraction_method": "Custom_Fallback_Node",
            }

        state = execute_async_agent_graph(
            input_data={"pdf_content": "corrupted pdf"},
            max_retries=3,
            initial_delay=0.01,
            backoff_factor=2.0,
            primary_extractor_fn=AlwaysFailingExtractor,
            fallback_extractor_fn=CustomFallbackExtractor,
        )

        self.assertEqual(state.status, GraphStatus.FALLBACK_SUCCESS)
        self.assertTrue(state.fallback_triggered)
        self.assertEqual(state.retry_counts.get("PRIMARY_EXTRACTOR"), 3)
        self.assertGreaterEqual(len(state.errors), 3)
        self.assertEqual(state.extracted_data.get("invoice_id"), "INV-FALLBACK-RECOVERED")
        self.assertEqual(state.extracted_data.get("extraction_method"), "Custom_Fallback_Node")

    def test_state_schema_validation(self):
        """Verify StateSchema validates state invariants and rejects invalid states."""
        valid_state = AgentGraphState(
            task_id="valid-id-123",
            input_data={"key": "val"},
            status=GraphStatus.PENDING,
        )
        self.assertTrue(StateSchema.validate(valid_state))

        # Invalid task_id
        invalid_state_1 = AgentGraphState(task_id="")
        with self.assertRaises(ValueError):
            StateSchema.validate(invalid_state_1)

        # Invalid status
        invalid_state_2 = AgentGraphState(status="UNKNOWN_STATUS")
        with self.assertRaises(ValueError):
            StateSchema.validate(invalid_state_2)

        # Invalid max_retries
        invalid_state_3 = AgentGraphState(max_retries=0)
        with self.assertRaises(ValueError):
            StateSchema.validate(invalid_state_3)

    def test_async_graph_concurrency(self):
        """Verify asynchronous non-blocking state machine execution under concurrent workloads."""
        async def run_concurrent_graphs():
            graph = AsyncAgentGraphStateMachine()
            states = [
                AgentGraphState(input_data={"invoice_id": f"CONCURRENT-{i}"}, initial_delay=0.01)
                for i in range(5)
            ]
            results = await asyncio.gather(*(graph.run(s) for s in states))
            return results

        results = asyncio.run(run_concurrent_graphs())
        self.assertEqual(len(results), 5)
        for idx, res in enumerate(results):
            self.assertEqual(res.status, GraphStatus.SUCCESS)
            self.assertEqual(res.extracted_data.get("invoice_id"), f"CONCURRENT-{idx}")
