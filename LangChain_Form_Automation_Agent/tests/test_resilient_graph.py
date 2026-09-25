"""
Unit Tests for Resilient Multi-Node Agent Execution Graph (CR-1495).

Verifies all CR-1495 requirements:
1. Successful graph execution
2. Transient failure followed by successful conditional retry
3. Retry exhaustion routing to fallback/recovery
4. Fatal failure routing immediately to recovery (zero pointless retries)
5. Fallback/recovery path execution and state preservation
6. Recovery failure containment
7. State schema validation
8. Conditional edge routing
9. Bounded exponential backoff calculation and execution
10. Execution trace recording of actual graph traversal
11. Asynchronous multi-agent execution (ainvoke)
12. Real-world mocked LLM, SMTP, and sheet failure scenarios (zero external network calls)
"""

import asyncio
import sys
import unittest
from pathlib import Path
from typing import TypedDict, List, Optional
from unittest.mock import MagicMock, patch

# Ensure paths are set
project_dir = str(Path(__file__).resolve().parent.parent)
task_dir = str(Path(__file__).resolve().parent.parent / "langchain task")
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
if task_dir not in sys.path:
    sys.path.insert(0, task_dir)

from resilient_graph import (
    StateGraph,
    END,
    START,
    StateValidationError,
    classify_error,
    calculate_backoff_delay,
    execute_backoff,
    execute_backoff_async,
    validate_state,
)
import email_langchain


class SampleGraphSchema(TypedDict):
    question: str
    answer: str


class TestResilientGraphCore(unittest.TestCase):
    """Core state machine, backoff, and validation tests."""

    def test_successful_execution(self):
        """Requirement 1: Normal success through all nodes."""
        graph = StateGraph()
        graph.add_node("step1", lambda s: {"step1": True})
        graph.add_node("step2", lambda s: {"step2": True})
        graph.set_entry_point("step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", END)

        app = graph.compile()
        result = app.invoke({"input": "test"})

        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("step1"))
        self.assertTrue(result.get("step2"))
        self.assertEqual(result.get("trace"), ["step1", "step2"])

    def test_transient_failure_and_conditional_retry(self):
        """Requirement 2: Transient failure triggers conditional retry edge to re-execute node."""
        mock_sleep = MagicMock()
        attempts = 0

        def flaky_node(state):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return {
                    "error": "429 RateLimit",
                    "error_type": "transient",
                    "retry_count": 1,
                    "status": "retrying"
                }
            return {
                "result": "recovered",
                "error": None,
                "error_type": None,
                "retry_count": 0,
                "status": "success"
            }

        def route_fn(state):
            if state.get("error_type") == "transient":
                execute_backoff(state["retry_count"], sleep_fn=mock_sleep)
                return "retry"
            return "next"

        graph = StateGraph()
        graph.add_node("flaky", flaky_node)
        graph.add_node("finish", lambda s: {"done": True})
        graph.set_entry_point("flaky")
        graph.add_conditional_edges("flaky", route_fn, {"retry": "flaky", "next": "finish"})
        graph.add_edge("finish", END)

        app = graph.compile()
        result = app.invoke({})

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("result"), "recovered")
        self.assertEqual(attempts, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        # Graph trace clearly shows 'flaky' visited twice via the conditional retry edge!
        self.assertEqual(result.get("trace"), ["flaky", "flaky", "finish"])

    def test_retry_exhaustion_routes_to_recovery(self):
        """Requirement 4: Exceeded retries route to recovery path."""
        mock_sleep = MagicMock()
        attempts = 0

        def failing_node(state):
            nonlocal attempts
            attempts += 1
            retries = state.get("retry_count", 0) + 1
            return {
                "error": "Persistent Timeout",
                "error_type": "transient",
                "retry_count": retries,
                "status": "retrying"
            }

        def recovery_node(state):
            return {
                "recovery_status": "recovered",
                "status": "recovered",
                "final_data": "fallback_payload"
            }

        def route_fn(state):
            retries = state.get("retry_count", 0)
            if state.get("error_type") == "transient":
                if retries <= 2:
                    execute_backoff(retries, sleep_fn=mock_sleep)
                    return "retry"
                return "fallback"
            return "next"

        graph = StateGraph()
        graph.add_node("failing", failing_node)
        graph.add_node("recovery", recovery_node)
        graph.set_entry_point("failing")
        graph.add_conditional_edges("failing", route_fn, {"retry": "failing", "fallback": "recovery"})
        graph.add_edge("recovery", END)

        app = graph.compile()
        result = app.invoke({})

        self.assertEqual(result.get("status"), "recovered")
        self.assertEqual(result.get("recovery_status"), "recovered")
        self.assertEqual(result.get("final_data"), "fallback_payload")
        self.assertEqual(attempts, 3)  # Initial + 2 retries
        self.assertEqual(result.get("trace"), ["failing", "failing", "failing", "recovery"])

    def test_fatal_failure_routes_without_retries(self):
        """Requirement 5: Fatal error routes immediately to recovery with zero retries."""
        mock_sleep = MagicMock()
        attempts = 0

        def fatal_node(state):
            nonlocal attempts
            attempts += 1
            return {
                "error": "401 Unauthorized",
                "error_type": "fatal",
                "status": "fatal"
            }

        def recovery_node(state):
            return {"recovery_status": "recovered", "status": "recovered"}

        def route_fn(state):
            if state.get("error_type") == "fatal":
                return "fallback"
            return "next"

        graph = StateGraph()
        graph.add_node("fatal", fatal_node)
        graph.add_node("recovery", recovery_node)
        graph.set_entry_point("fatal")
        graph.add_conditional_edges("fatal", route_fn, {"fallback": "recovery"})
        graph.add_edge("recovery", END)

        app = graph.compile()
        result = app.invoke({})

        self.assertEqual(attempts, 1)  # EXACTLY 1 attempt, zero retries
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(result.get("status"), "recovered")
        self.assertEqual(result.get("trace"), ["fatal", "recovery"])

    def test_recovery_failure_containment(self):
        """Requirement 6: Safe containment when recovery node itself throws."""
        def failing_node(state):
            return {"error": "first_error"}

        def broken_recovery(state):
            raise RuntimeError("Recovery exploded")

        graph = StateGraph()
        graph.add_node("fail", failing_node)
        graph.add_node("recovery", broken_recovery)
        graph.set_entry_point("fail")
        graph.add_edge("fail", "recovery")
        graph.add_edge("recovery", END)

        app = graph.compile()
        result = app.invoke({})

        self.assertEqual(result.get("status"), "failed")
        self.assertIn("Recovery exploded", result.get("error", ""))

    def test_state_validation(self):
        """Requirement 6: State schema and type validation."""
        valid_state = {"question": "What is Python?", "answer": "A language"}
        validate_state(valid_state, SampleGraphSchema)

        # Missing required key
        with self.assertRaises(StateValidationError):
            validate_state({"question": "Missing answer"}, SampleGraphSchema)

        # Type mismatch
        with self.assertRaises(StateValidationError):
            validate_state({"question": 12345, "answer": "Answer"}, SampleGraphSchema)

    def test_exponential_backoff_calculation(self):
        """Requirement 3: Exponential backoff delay calculation and cap."""
        # attempt 1: 0.1 * 2^0 = 0.1
        self.assertAlmostEqual(calculate_backoff_delay(1, base_delay=0.1, factor=2.0, max_delay=1.0), 0.1)
        # attempt 2: 0.1 * 2^1 = 0.2
        self.assertAlmostEqual(calculate_backoff_delay(2, base_delay=0.1, factor=2.0, max_delay=1.0), 0.2)
        # attempt 3: 0.1 * 2^2 = 0.4
        self.assertAlmostEqual(calculate_backoff_delay(3, base_delay=0.1, factor=2.0, max_delay=1.0), 0.4)
        # attempt 4: 0.1 * 2^3 = 0.8
        self.assertAlmostEqual(calculate_backoff_delay(4, base_delay=0.1, factor=2.0, max_delay=1.0), 0.8)
        # attempt 5: 0.1 * 2^4 = 1.6 -> capped at max_delay 1.0
        self.assertAlmostEqual(calculate_backoff_delay(5, base_delay=0.1, factor=2.0, max_delay=1.0), 1.0)

    def test_async_graph_execution(self):
        """Requirement 4 & 9: Genuine asynchronous state machine execution (ainvoke)."""
        async def run_test():
            mock_async_sleep = MagicMock()
            attempts = 0

            async def async_flaky(state):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    return {
                        "error": "Async 429",
                        "error_type": "transient",
                        "retry_count": 1,
                        "status": "retrying"
                    }
                await asyncio.sleep(0)  # genuine await
                return {"result": "async_ok", "error": None, "error_type": None, "status": "success"}

            async def async_route(state):
                if state.get("error_type") == "transient":
                    await execute_backoff_async(state["retry_count"], async_sleep_fn=mock_async_sleep)
                    return "retry"
                return "next"

            graph = StateGraph()
            graph.add_node("step", async_flaky)
            graph.set_entry_point("step")
            graph.add_conditional_edges("step", async_route, {"retry": "step", "next": END})

            app = graph.compile()
            result = await app.ainvoke({})

            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("result"), "async_ok")
            self.assertEqual(attempts, 2)
            self.assertEqual(mock_async_sleep.call_count, 1)
            self.assertEqual(result.get("trace"), ["step", "step"])

        asyncio.run(run_test())


class TestEmailLangChainWorkflow(unittest.TestCase):
    """Workflow-specific tests for email_langchain.py."""

    def test_email_workflow_success_mocked(self):
        """End-to-end success in email_langchain with mocked sheet, LLM, and SMTP."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Paris is the capital of France."

        graph = email_langchain.create_email_agent_graph(llm_client=mock_llm)
        app = graph.compile()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value = MagicMock()

            initial_state = {
                "email": "user@example.com",
                "question": "What is the capital of France?"
            }
            result = app.invoke(initial_state)

            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("answer"), "Paris is the capital of France.")
            self.assertEqual(result.get("email_status"), "sent")
            self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "send_email"])

    def test_email_workflow_llm_transient_retry(self):
        """LLM node recovers from transient 429 rate limit via conditional retry edge."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [
            Exception("429 Too Many Requests"),
            MagicMock(content="Retry succeeded")
        ]

        mock_sleep = MagicMock()
        graph = email_langchain.create_email_agent_graph(
            llm_client=mock_llm,
            max_retries=2,
            sleep_fn=mock_sleep
        )
        app = graph.compile()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value = MagicMock()

            initial_state = {
                "email": "user@example.com",
                "question": "Query"
            }
            result = app.invoke(initial_state)

            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("answer"), "Retry succeeded")
            self.assertEqual(mock_sleep.call_count, 1)
            # The execution trace proves actual graph traversal: llm_answer was entered twice!
            self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "llm_answer", "send_email"])

    def test_email_workflow_llm_exhaustion_fallback(self):
        """Persistent LLM failure exhausts retries and transitions to recovery node."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("429 Persistent Rate Limit")

        mock_sleep = MagicMock()
        graph = email_langchain.create_email_agent_graph(
            llm_client=mock_llm,
            max_retries=2,
            sleep_fn=mock_sleep
        )
        app = graph.compile()

        initial_state = {
            "email": "user@example.com",
            "question": "How do airplanes fly?"
        }
        result = app.invoke(initial_state)

        self.assertEqual(result.get("status"), "recovered")
        self.assertEqual(result.get("recovery_status"), "recovered")
        self.assertIn("operating in fallback mode", result.get("answer", ""))
        self.assertEqual(mock_sleep.call_count, 2)
        # Visited llm_answer 3 times (1 initial + 2 retries), then routed to recovery!
        self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "llm_answer", "llm_answer", "recovery"])

    def test_email_workflow_smtp_transient_retry(self):
        """SMTP delivery recovers from transient network timeout via conditional retry edge."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer text"

        mock_sleep = MagicMock()
        graph = email_langchain.create_email_agent_graph(
            llm_client=mock_llm,
            max_retries=2,
            sleep_fn=mock_sleep
        )
        app = graph.compile()

        # SMTP fails on attempt 1, succeeds on attempt 2
        mock_smtp = MagicMock()
        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.side_effect = [
            ConnectionResetError("Connection reset by peer"),
            smtp_instance
        ]

        with patch("smtplib.SMTP", mock_smtp):
            initial_state = {
                "email": "user@example.com",
                "question": "Hello"
            }
            result = app.invoke(initial_state)

            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("email_status"), "sent")
            self.assertEqual(mock_sleep.call_count, 1)
            # send_email was entered twice via conditional retry edge!
            self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "send_email", "send_email"])

    def test_email_workflow_smtp_exhaustion_recovery(self):
        """Persistent SMTP failure exhausts retries and transitions to recovery node."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer text"

        mock_sleep = MagicMock()
        graph = email_langchain.create_email_agent_graph(
            llm_client=mock_llm,
            max_retries=1,
            sleep_fn=mock_sleep
        )
        app = graph.compile()

        with patch("smtplib.SMTP", side_effect=ConnectionError("Server unreachable")):
            initial_state = {
                "email": "user@example.com",
                "question": "Hello"
            }
            result = app.invoke(initial_state)

            self.assertEqual(result.get("status"), "recovered")
            self.assertEqual(result.get("recovery_status"), "recovered")
            self.assertEqual(result.get("email_status"), "queued_offline")
            self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "send_email", "send_email", "recovery"])

    def test_email_workflow_fatal_recipient_recovery(self):
        """Fatal error (invalid email format) routes directly to recovery without retries."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer text"

        mock_sleep = MagicMock()
        graph = email_langchain.create_email_agent_graph(
            llm_client=mock_llm,
            max_retries=3,
            sleep_fn=mock_sleep
        )
        app = graph.compile()

        initial_state = {
            "email": "invalid_email_without_at_sign",
            "question": "Hello"
        }
        result = app.invoke(initial_state)

        self.assertEqual(result.get("status"), "recovered")
        self.assertEqual(result.get("recovery_status"), "recovered")
        self.assertEqual(mock_sleep.call_count, 0)  # Zero retries for fatal error!
        self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "send_email", "recovery"])

    def test_email_workflow_async_execution(self):
        """Asynchronous execution of email_langchain with ainvoke."""
        async def run_async():
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = "Async Answer"
            mock_async_sleep = MagicMock()

            graph = email_langchain.create_email_agent_graph(
                llm_client=mock_llm,
                is_async=True,
                async_sleep_fn=mock_async_sleep
            )
            app = graph.compile()

            with patch("smtplib.SMTP") as mock_smtp:
                mock_smtp.return_value.__enter__.return_value = MagicMock()

                initial_state = {
                    "email": "user@example.com",
                    "question": "Async question"
                }
                result = await app.ainvoke(initial_state)

                self.assertEqual(result.get("status"), "success")
                self.assertEqual(result.get("answer"), "Async Answer")
                self.assertEqual(result.get("email_status"), "sent")
                self.assertEqual(result.get("trace"), ["get_input", "llm_answer", "send_email"])

        asyncio.run(run_async())

    def test_email_workflow_sheet_transient_retry(self):
        """Google Sheet read encounters transient error, retries via conditional retry edge, and succeeds."""
        mock_sleep = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iloc = [{"Email": "sheet_user@example.com", "Ask your question here !": "Sheet question"}]

        with patch("email_langchain.pd") as mock_pd:
            mock_pd.read_csv.side_effect = [
                ConnectionError("Sheet connection timeout"),
                mock_df
            ]

            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = "Answer from sheet"

            graph = email_langchain.create_email_agent_graph(
                llm_client=mock_llm,
                max_retries=2,
                sleep_fn=mock_sleep
            )
            app = graph.compile()

            with patch("smtplib.SMTP") as mock_smtp:
                mock_smtp.return_value.__enter__.return_value = MagicMock()

                result = app.invoke({})

                self.assertEqual(result.get("status"), "success")
                self.assertEqual(result.get("email"), "sheet_user@example.com")
                self.assertEqual(mock_sleep.call_count, 1)
                self.assertEqual(result.get("trace"), ["get_input", "get_input", "llm_answer", "send_email"])


    def test_email_workflow_sheet_exhaustion_recovery(self):
        """Persistent Google Sheet failure exhausts retries and routes to recovery."""
        mock_sleep = MagicMock()

        with patch("email_langchain.pd") as mock_pd:
            mock_pd.read_csv.side_effect = ConnectionError("Persistent network failure")

            graph = email_langchain.create_email_agent_graph(
                max_retries=2,
                sleep_fn=mock_sleep
            )
            app = graph.compile()

            result = app.invoke({})

            self.assertEqual(result.get("status"), "recovered")
            self.assertEqual(result.get("recovery_status"), "recovered")
            self.assertEqual(mock_sleep.call_count, 2)
            self.assertEqual(result.get("trace"), ["get_input", "get_input", "get_input", "recovery"])


class TestFormAgents(unittest.TestCase):
    """Unit tests for standalone and supabase form agents."""

    def test_supabase_form_agent_pipeline(self):
        import supabase_form_agent
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.columns = ["Email", "Ask your question here !", "Name", "phone no"]
        mock_df.iloc = [{"Email": "alice@example.com", "Ask your question here !": "How to contribute?", "Name": "Alice", "phone no": "12345"}]

        with patch("supabase_form_agent.pd.read_csv", return_value=mock_df), \
             patch("supabase_form_agent.get_llm") as mock_llm_fn, \
             patch("smtplib.SMTP") as mock_smtp:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = "Fork the repo and create a PR."
            mock_llm_fn.return_value = mock_llm
            mock_smtp.return_value.__enter__.return_value = MagicMock()

            app = supabase_form_agent.build_supabase_form_agent()
            result = app.invoke({})

            self.assertEqual(result.get("email"), "alice@example.com")
            self.assertEqual(result.get("answer"), "Fork the repo and create a PR.")
            self.assertEqual(result.get("name"), "Alice")

    def test_sheet_webhook_agent_save(self):
        import sheet_webhook_agent
        with patch("sheet_webhook_agent.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            res = sheet_webhook_agent.save_answer_to_sheet("Test answer")
            self.assertIsNotNone(res)
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
