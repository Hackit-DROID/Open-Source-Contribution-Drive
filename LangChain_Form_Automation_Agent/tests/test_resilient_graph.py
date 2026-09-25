"""
Comprehensive Unit Tests for Resilient Agent Execution Graph (CR-1491).
Tests cover:
- Test 1: Normal success (A -> B -> C -> SUCCESS)
- Test 2: Retryable failure recovered (A -> B fails -> retry B -> B succeeds -> C)
- Test 3: Retry exhaustion (B fails repeatedly -> retry limit -> recovery -> controlled termination)
- Test 4: Fatal failure (B produces fatal error -> recovery immediately, no retry loop)
- Test 5: Recovery success (failed node -> fallback handler -> continuation/recovered state)
- Test 6: Recovery failure (recovery handler itself throws -> safe containment without crash)
- Test 7: State schema validation (valid state accepted, missing/invalid types rejected)
- Test 8: Conditional routing (conditional branch decisions)
- Test 9: Bounded exponential backoff policy (increasing delays, bounded max_delay, mocked sleep)
- Test 10: Exception & error preservation (retains original error type, message, and node)
- Test 11: Graph traversal trace verification (asserting exact node sequences)
- Test 12: Zero real waiting during tests (mocked sleep functions)
"""

import sys
import unittest
from pathlib import Path
from typing import TypedDict
from unittest.mock import MagicMock

# Ensure parent directory is on sys.path
agent_dir = str(Path(__file__).resolve().parent.parent)
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from resilient_graph import (
    END,
    START,
    AgentState,
    ErrorCategory,
    ExecutionStatus,
    FatalNodeError,
    ResilientStateGraph,
    RetryExhaustedError,
    RetryPolicy,
    StateValidationError,
    TransientNodeError,
    classify_error,
    default_error_classifier,
)


class SampleStateSchema(TypedDict):
    question: str
    processed: str
    answer: str


class TestResilientGraph(unittest.TestCase):
    """Test suite for CR-1491 Resilient Multi-Node Agent Execution Graph."""

    def setUp(self):
        # Mock sleep function to ensure zero real waiting
        self.mock_sleep = MagicMock()

    # -------------------------------------------------------------
    # Test 1: Normal Successful Execution (A -> B -> C -> SUCCESS)
    # -------------------------------------------------------------
    def test_normal_successful_execution(self):
        """Verify normal linear flow: node_a -> node_b -> node_c -> SUCCESS."""
        def node_a(state):
            return {"question": state["question"], "step_a": True}

        def node_b(state):
            return {"processed": state["question"].upper(), "step_b": True}

        def node_c(state):
            return {"answer": f"Done: {state['processed']}", "step_c": True}

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b)
        graph.add_node("node_c", node_c)

        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", "node_c")
        graph.add_edge("node_c", END)
        graph.set_entry_point("node_a")

        app = graph.compile()
        initial_state = {"question": "hello world"}
        result = app.invoke(initial_state)

        # Assert status and results
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result["answer"], "Done: HELLO WORLD")
        self.assertTrue(result.get("step_a"))
        self.assertTrue(result.get("step_b"))
        self.assertTrue(result.get("step_c"))
        self.assertIsNone(result.last_error)

        # Assert exact execution traversal
        expected_trace = ["node_a", "node_b", "node_c"]
        self.assertEqual(result.execution_trace, expected_trace)

    # -------------------------------------------------------------
    # Test 2: Retryable Failure Recovered (Transient failure -> Retry -> Success)
    # -------------------------------------------------------------
    def test_retryable_failure_recovered(self):
        """Verify transient failure at Node B triggers backoff and retry, then succeeds."""
        attempts = 0

        def node_a(state):
            return {"question": state["question"]}

        def node_b(state):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                # First attempt fails with transient timeout
                raise TimeoutError("Simulated temporary gateway timeout")
            return {"processed": state["question"].upper()}

        def node_c(state):
            return {"answer": f"Result: {state['processed']}"}

        retry_policy = RetryPolicy(
            max_retries=2,
            base_delay=1.0,
            factor=2.0,
            sleep_fn=self.mock_sleep,
        )

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b, retry_policy=retry_policy)
        graph.add_node("node_c", node_c)

        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", "node_c")
        graph.add_edge("node_c", END)
        graph.set_entry_point("node_a")

        app = graph.compile()
        result = app.invoke({"question": "test retry"})

        # Node B should have executed twice (1 failure + 1 success)
        self.assertEqual(attempts, 2)
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result["answer"], "Result: TEST RETRY")

        # Sleep function was invoked with base_delay (1.0s)
        self.mock_sleep.assert_called_once_with(1.0)

        # Verify trace has retry recorded
        expected_trace = ["node_a", "node_b", "retry:node_b:1", "node_b", "node_c"]
        self.assertEqual(result.execution_trace, expected_trace)

    # -------------------------------------------------------------
    # Test 3: Retry Exhaustion (Retries fail -> Limit reached -> Recovery)
    # -------------------------------------------------------------
    def test_retry_exhaustion_routes_to_recovery(self):
        """Verify that when retries are exhausted, execution transitions to fallback recovery."""
        b_calls = 0

        def node_a(state):
            return {"question": state["question"]}

        def node_b(state):
            nonlocal b_calls
            b_calls += 1
            raise ConnectionError("Persistent network outage")

        def fallback_b(state, error):
            return {"processed": "FALLBACK_VALUE", "fallback_reason": str(error)}

        def node_c(state):
            return {"answer": f"Processed with: {state['processed']}"}

        retry_policy = RetryPolicy(
            max_retries=2,
            base_delay=0.5,
            factor=2.0,
            sleep_fn=self.mock_sleep,
        )

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b, retry_policy=retry_policy, fallback_handler=fallback_b)
        graph.add_node("node_c", node_c)

        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", "node_c")
        graph.add_edge("node_c", END)
        graph.set_entry_point("node_a")

        app = graph.compile()
        result = app.invoke({"question": "exhaustion test"})

        # Initial attempt + 2 retries = 3 calls
        self.assertEqual(b_calls, 3)
        self.assertEqual(result.recovery_status, "recovered")
        self.assertEqual(result["processed"], "FALLBACK_VALUE")
        self.assertEqual(result["answer"], "Processed with: FALLBACK_VALUE")

        # Mock sleep called twice: 0.5s then 1.0s
        self.assertEqual(self.mock_sleep.call_count, 2)
        self.mock_sleep.assert_any_call(0.5)
        self.mock_sleep.assert_any_call(1.0)

        # Trace checks
        expected_trace = [
            "node_a",
            "node_b",
            "retry:node_b:1",
            "node_b",
            "retry:node_b:2",
            "node_b",
            "exhausted:node_b",
            "fallback:node_b",
            "node_c",
        ]
        self.assertEqual(result.execution_trace, expected_trace)

    # -------------------------------------------------------------
    # Test 4: Fatal Non-Retryable Failure (No retry loop, direct recovery)
    # -------------------------------------------------------------
    def test_fatal_failure_routes_immediately_to_recovery(self):
        """Verify fatal non-retryable errors skip retries and route directly to recovery."""
        b_calls = 0

        def node_a(state):
            return {"question": state["question"]}

        def node_b(state):
            nonlocal b_calls
            b_calls += 1
            raise ValueError("Invalid schema: fatal parse failure")

        def fallback_b(state, error):
            return {"processed": "FATAL_FALLBACK", "fatal_error": type(error).__name__}

        retry_policy = RetryPolicy(max_retries=5, sleep_fn=self.mock_sleep)

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a)
        graph.add_node("node_b", node_b, retry_policy=retry_policy, fallback_handler=fallback_b)
        graph.set_entry_point("node_a")
        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", END)

        app = graph.compile()
        result = app.invoke({"question": "fatal test"})

        # Crucial check: called exactly ONCE. Did NOT loop or retry.
        self.assertEqual(b_calls, 1)
        self.mock_sleep.assert_not_called()
        self.assertEqual(result.error_classification, ErrorCategory.FATAL)
        self.assertEqual(result["processed"], "FATAL_FALLBACK")
        self.assertEqual(result["fatal_error"], "ValueError")

        expected_trace = ["node_a", "node_b", "fatal:node_b", "fallback:node_b"]
        self.assertEqual(result.execution_trace, expected_trace)

    # -------------------------------------------------------------
    # Test 5: Recovery Handler Success and State Preservation
    # -------------------------------------------------------------
    def test_recovery_success_preserves_state(self):
        """Verify recovery handler preserves accumulated state and original error information."""
        def node_a(state):
            return {"account_id": "ACC-1234", "balance": 500}

        def node_b(state):
            raise TransientNodeError("Rate limit 429 exceeded on payments gateway")

        def fallback_b(state, error):
            # Preserves original state, sets degraded fallback data
            return {"payment_status": "queued_offline", "degraded": True}

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a)
        graph.add_node(
            "node_b",
            node_b,
            retry_policy=RetryPolicy(max_retries=1, sleep_fn=self.mock_sleep),
            fallback_handler=fallback_b,
        )
        graph.add_edge("node_a", "node_b")
        graph.add_edge("node_b", END)
        graph.set_entry_point("node_a")

        app = graph.compile()
        result = app.invoke({})

        # Prior accumulated state is intact
        self.assertEqual(result["account_id"], "ACC-1234")
        self.assertEqual(result["balance"], 500)
        self.assertEqual(result["payment_status"], "queued_offline")
        self.assertTrue(result["degraded"])
        self.assertEqual(result.recovery_status, "recovered")
        self.assertEqual(result.status, ExecutionStatus.RECOVERED)

    # -------------------------------------------------------------
    # Test 6: Safe Containment of Recovery Failure
    # -------------------------------------------------------------
    def test_recovery_failure_handled_safely(self):
        """Verify that an exception inside the recovery handler itself does not cause an unhandled crash."""
        def node_a(state):
            raise FatalNodeError("Initial node failure")

        def broken_fallback(state, error):
            raise RuntimeError("Database connection died during fallback!")

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a, fallback_handler=broken_fallback)
        graph.set_entry_point("node_a")
        graph.add_edge("node_a", END)

        app = graph.compile()
        # invoke() must NOT raise an unhandled exception
        result = app.invoke({"input": "test"})

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.recovery_status, "failed")
        self.assertIn("Fallback error", result.last_error)
        self.assertIn("fallback_failed:node_a", result.execution_trace)

    # -------------------------------------------------------------
    # Test 7: State Schema Validation
    # -------------------------------------------------------------
    def test_state_validation_rejects_missing_and_invalid_types(self):
        """Verify schema validation enforces required keys and types."""
        class StrictSchema(TypedDict):
            user_id: int
            query: str

        graph = ResilientStateGraph(state_schema=StrictSchema)
        graph.add_node("dummy", lambda s: s)
        graph.set_entry_point("dummy")
        graph.add_edge("dummy", END)

        app = graph.compile()

        # 1. Missing required key
        with self.assertRaises(StateValidationError) as ctx:
            app.invoke({"user_id": 42})
        self.assertIn("Missing required state key: 'query'", str(ctx.exception))

        # 2. Invalid type for key
        with self.assertRaises(StateValidationError) as ctx:
            app.invoke({"user_id": "not_an_int", "query": "hello"})
        self.assertIn("State key 'user_id' expected type int", str(ctx.exception))

        # 3. Valid state passes
        valid_res = app.invoke({"user_id": 42, "query": "hello"})
        self.assertEqual(valid_res.status, ExecutionStatus.SUCCESS)

    # -------------------------------------------------------------
    # Test 8: Conditional Edge Routing
    # -------------------------------------------------------------
    def test_conditional_edge_routing(self):
        """Verify conditional edges route dynamically based on state."""
        def router(state):
            score = state.get("score", 0)
            return "high" if score >= 80 else "low"

        def high_node(state):
            return {"grade": "A"}

        def low_node(state):
            return {"grade": "C"}

        graph = ResilientStateGraph()
        graph.add_node("start_node", lambda s: s)
        graph.add_node("high_node", high_node)
        graph.add_node("low_node", low_node)

        graph.set_entry_point("start_node")
        graph.add_conditional_edges(
            "start_node",
            router,
            {"high": "high_node", "low": "low_node"},
        )
        graph.add_edge("high_node", END)
        graph.add_edge("low_node", END)

        app = graph.compile()

        # Route High
        res_high = app.invoke({"score": 95})
        self.assertEqual(res_high["grade"], "A")
        self.assertEqual(res_high.execution_trace, ["start_node", "high_node"])

        # Route Low
        res_low = app.invoke({"score": 50})
        self.assertEqual(res_low["grade"], "C")
        self.assertEqual(res_low.execution_trace, ["start_node", "low_node"])

    # -------------------------------------------------------------
    # Test 9: Bounded Exponential Backoff Delays
    # -------------------------------------------------------------
    def test_exponential_backoff_delays_and_bounds(self):
        """Verify backoff delays calculate exponential increases and obey maximum bound."""
        policy = RetryPolicy(max_retries=5, base_delay=1.0, factor=2.0, max_delay=8.0)

        # Attempt 0 -> 0.0s
        self.assertEqual(policy.calculate_delay(0), 0.0)
        # Attempt 1 -> 1.0 * (2^0) = 1.0s
        self.assertEqual(policy.calculate_delay(1), 1.0)
        # Attempt 2 -> 1.0 * (2^1) = 2.0s
        self.assertEqual(policy.calculate_delay(2), 2.0)
        # Attempt 3 -> 1.0 * (2^2) = 4.0s
        self.assertEqual(policy.calculate_delay(3), 4.0)
        # Attempt 4 -> 1.0 * (2^3) = 8.0s (reaches max_delay)
        self.assertEqual(policy.calculate_delay(4), 8.0)
        # Attempt 5 -> capped at max_delay = 8.0s
        self.assertEqual(policy.calculate_delay(5), 8.0)

    # -------------------------------------------------------------
    # Test 10: Error Classification Logic
    # -------------------------------------------------------------
    def test_error_classification(self):
        """Verify default error classifier categorizes transient vs fatal exceptions."""
        self.assertEqual(default_error_classifier(TimeoutError()), ErrorCategory.RETRYABLE)
        self.assertEqual(default_error_classifier(ConnectionResetError()), ErrorCategory.RETRYABLE)
        self.assertEqual(default_error_classifier(TransientNodeError()), ErrorCategory.RETRYABLE)
        self.assertEqual(default_error_classifier(Exception("Rate limit 429")), ErrorCategory.RETRYABLE)

        self.assertEqual(default_error_classifier(ValueError()), ErrorCategory.FATAL)
        self.assertEqual(default_error_classifier(TypeError()), ErrorCategory.FATAL)
        self.assertEqual(default_error_classifier(KeyError()), ErrorCategory.FATAL)
        self.assertEqual(default_error_classifier(FatalNodeError()), ErrorCategory.FATAL)
        self.assertEqual(default_error_classifier(Exception("Unauthorized 401")), ErrorCategory.FATAL)

    # -------------------------------------------------------------
    # Test 11: Dedicated Global Recovery Node
    # -------------------------------------------------------------
    def test_global_recovery_node(self):
        """Verify graph transitions to dedicated recovery node when configured."""
        def node_a(state):
            raise TransientNodeError("Network timeout on external provider")

        def global_recovery(state):
            state.recovery_status = "recovered"
            state.status = ExecutionStatus.RECOVERED
            return {"recovered_by": "global_recovery_node", "preserved_data": state.get("key")}

        graph = ResilientStateGraph()
        graph.add_node("node_a", node_a, retry_policy=RetryPolicy(max_retries=1, sleep_fn=self.mock_sleep))
        graph.set_entry_point("node_a")
        graph.set_recovery_node("recovery_handler", global_recovery)

        app = graph.compile()
        result = app.invoke({"key": "val123"})

        self.assertEqual(result.status, ExecutionStatus.RECOVERED)
        self.assertEqual(result["recovered_by"], "global_recovery_node")
        self.assertEqual(result["preserved_data"], "val123")
        expected_trace = ["node_a", "retry:node_a:1", "node_a", "exhausted:node_a", "recovery_handler"]
        self.assertEqual(result.execution_trace, expected_trace)

    # -------------------------------------------------------------
    # Test 12: Original Exception Preservation
    # -------------------------------------------------------------
    def test_exception_preservation(self):
        """Verify original exception object and message are preserved in execution state."""
        class CustomTestError(Exception):
            pass

        original_exc = CustomTestError("Custom failure message with diagnostics")

        def failing_node(state):
            raise original_exc

        graph = ResilientStateGraph()
        graph.add_node("failing_node", failing_node, retry_policy=RetryPolicy(max_retries=0))
        graph.set_entry_point("failing_node")
        graph.add_edge("failing_node", END)

        app = graph.compile()
        result = app.invoke({})

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.last_exception, original_exc)
        self.assertIn("Custom failure message with diagnostics", result.last_error)
        self.assertEqual(result.error_classification, ErrorCategory.FATAL)


if __name__ == "__main__":
    unittest.main()
