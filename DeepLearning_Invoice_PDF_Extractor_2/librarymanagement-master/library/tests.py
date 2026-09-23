import asyncio
from unittest.mock import AsyncMock, MagicMock

from django.test import SimpleTestCase

from .graph import (
    END,
    GraphError,
    NodeFailedError,
    RetryPolicy,
    StateGraph,
    StateValidationError,
)


class FakeSleep:
    def __init__(self):
        self.delays = []

    async def __call__(self, delay):
        self.delays.append(delay)


def run(graph, state):
    return asyncio.run(graph.run(state))


class RetryPolicyTests(SimpleTestCase):
    def test_exponential_backoff(self):
        policy = RetryPolicy(base_delay=0.5, backoff=2)
        self.assertEqual([policy.delay_for(n) for n in (1, 2, 3, 4)], [0.5, 1.0, 2.0, 4.0])

    def test_delay_is_capped(self):
        policy = RetryPolicy(base_delay=1, backoff=10, max_delay=5)
        self.assertEqual(policy.delay_for(3), 5)

    def test_jitter_stays_in_range(self):
        policy = RetryPolicy(base_delay=1, jitter=0.5)
        for _ in range(20):
            self.assertTrue(1 <= policy.delay_for(1) <= 1.5)

    def test_needs_at_least_one_attempt(self):
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)


class StateGraphTests(SimpleTestCase):
    def setUp(self):
        self.sleep = FakeSleep()

    def make_graph(self, **kwargs):
        return StateGraph(sleep=self.sleep, **kwargs)

    def test_runs_nodes_in_order_and_merges_state(self):
        graph = self.make_graph()
        graph.add_node("load", AsyncMock(return_value={"text": "raw"}))
        graph.add_node("parse", lambda state: {"parsed": state["text"].upper()})
        graph.add_edge("load", "parse")

        result = run(graph, {"file": "a.pdf"})

        self.assertEqual(result.path, ["load", "parse"])
        self.assertEqual(result.state, {"file": "a.pdf", "text": "raw", "parsed": "RAW"})
        self.assertFalse(result.recovered)

    def test_input_state_is_not_mutated(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: {"x": 1})
        initial = {"x": 0}

        run(graph, initial)

        self.assertEqual(initial, {"x": 0})

    def test_transient_failure_is_retried_with_backoff(self):
        extract = AsyncMock(side_effect=[ConnectionError("down"), TimeoutError("slow"), {"data": 42}])
        graph = self.make_graph()
        graph.add_node("extract", extract, retry=RetryPolicy(max_attempts=3, base_delay=1, backoff=2))

        result = run(graph, {})

        self.assertEqual(extract.await_count, 3)
        self.assertEqual(self.sleep.delays, [1, 2])
        self.assertEqual(result.state["data"], 42)
        self.assertEqual(result.steps[0].attempts, 3)
        self.assertEqual(result.steps[0].status, "ok")

    def test_non_retryable_error_skips_retries(self):
        extract = AsyncMock(side_effect=ValueError("bad input"))
        graph = self.make_graph()
        graph.add_node("extract", extract, retry=RetryPolicy(max_attempts=5, retry_on=(ConnectionError,)), fallback="manual")
        graph.add_node("manual", lambda state: {"source": "manual"})

        result = run(graph, {})

        self.assertEqual(extract.await_count, 1)
        self.assertEqual(self.sleep.delays, [])
        self.assertEqual(result.path, ["extract", "manual"])

    def test_failed_node_routes_to_fallback_and_pipeline_continues(self):
        llm = AsyncMock(side_effect=ConnectionError("api down"))
        rules = MagicMock(return_value={"fields": {"total": "10"}, "source": "rules"})
        save = MagicMock(return_value={"saved": True})

        graph = self.make_graph()
        graph.add_node("llm_extract", llm, retry=RetryPolicy(max_attempts=2, base_delay=0.1), fallback="rule_extract")
        graph.add_node("rule_extract", rules)
        graph.add_node("save", save)
        graph.add_edge("llm_extract", "save")
        graph.add_edge("rule_extract", "save")

        result = run(graph, {"file": "invoice.pdf"})

        self.assertEqual(result.path, ["llm_extract", "rule_extract", "save"])
        self.assertEqual([s.status for s in result.steps], ["failed", "ok", "ok"])
        self.assertTrue(result.recovered)
        self.assertEqual(llm.await_count, 2)
        self.assertEqual(result.state["source"], "rules")
        self.assertTrue(result.state["saved"])
        self.assertEqual(result.state["errors"][0]["node"], "llm_extract")
        self.assertIn("api down", result.state["errors"][0]["error"])
        save.assert_called_once()

    def test_fallback_chain(self):
        graph = self.make_graph()
        graph.add_node("primary", AsyncMock(side_effect=RuntimeError("x")), retry=RetryPolicy(max_attempts=1), fallback="secondary")
        graph.add_node("secondary", AsyncMock(side_effect=RuntimeError("y")), retry=RetryPolicy(max_attempts=1), fallback="last_resort")
        graph.add_node("last_resort", lambda state: {"done": True})

        result = run(graph, {})

        self.assertEqual(result.path, ["primary", "secondary", "last_resort"])
        self.assertEqual(len(result.state["errors"]), 2)

    def test_failure_without_fallback_raises(self):
        graph = self.make_graph()
        graph.add_node("extract", AsyncMock(side_effect=ConnectionError("down")), retry=RetryPolicy(max_attempts=2))

        with self.assertRaises(NodeFailedError) as ctx:
            run(graph, {})

        self.assertEqual(ctx.exception.node, "extract")
        self.assertIsInstance(ctx.exception.error, ConnectionError)

    def test_failed_attempt_does_not_leak_partial_state(self):
        def flaky(state):
            state["half_written"] = True
            raise ConnectionError("down")

        graph = self.make_graph()
        graph.add_node("flaky", flaky, retry=RetryPolicy(max_attempts=1), fallback="recover")
        graph.add_node("recover", lambda state: {"recovered": True})

        result = run(graph, {})

        self.assertNotIn("half_written", result.state)

    def test_timeout_counts_as_failure(self):
        async def slow(state):
            await asyncio.sleep(1)

        graph = self.make_graph()
        graph.add_node("slow", slow, timeout=0.01, retry=RetryPolicy(max_attempts=2), fallback="fast")
        graph.add_node("fast", lambda state: {"fast": True})

        result = run(graph, {})

        self.assertEqual(result.path, ["slow", "fast"])
        self.assertEqual(result.steps[0].attempts, 2)

    def test_conditional_edges(self):
        graph = self.make_graph()
        graph.add_node("check", lambda state: None)
        graph.add_node("approve", lambda state: {"status": "approved"})
        graph.add_node("review", lambda state: {"status": "review"})
        graph.add_conditional_edges(
            "check",
            lambda state: "high" if state["amount"] > 1000 else "low",
            {"high": "review", "low": "approve"},
        )

        self.assertEqual(run(graph, {"amount": 50}).state["status"], "approved")
        self.assertEqual(run(graph, {"amount": 5000}).state["status"], "review")

    def test_conditional_retry_edge_loops_until_valid(self):
        extract = AsyncMock(side_effect=[{"confidence": 0.3}, {"confidence": 0.6}, {"confidence": 0.95}])
        graph = self.make_graph()
        graph.add_node("extract", extract)
        graph.add_node("accept", lambda state: {"accepted": True})
        graph.add_conditional_edges(
            "extract",
            lambda state: "accept" if state["confidence"] >= 0.9 else "extract",
        )

        result = run(graph, {})

        self.assertEqual(result.path, ["extract", "extract", "extract", "accept"])
        self.assertTrue(result.state["accepted"])

    def test_router_can_end_graph(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: None)
        graph.add_node("b", MagicMock())
        graph.add_conditional_edges("a", lambda state: END)

        result = run(graph, {})

        self.assertEqual(result.path, ["a"])
        graph.nodes["b"].func.assert_not_called()

    def test_router_returning_unknown_route_raises(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: None)
        graph.add_conditional_edges("a", lambda state: "nope", {"yes": END})

        with self.assertRaises(GraphError):
            run(graph, {})

    def test_infinite_loop_is_stopped(self):
        graph = self.make_graph(max_steps=5)
        graph.add_node("a", lambda state: None)
        graph.add_edge("a", "a")

        with self.assertRaises(GraphError):
            run(graph, {})

    def test_schema_rejects_missing_key(self):
        graph = self.make_graph(schema={"file": str})
        graph.add_node("a", lambda state: None)

        with self.assertRaises(StateValidationError):
            run(graph, {})

    def test_schema_rejects_bad_update(self):
        graph = self.make_graph(schema={"file": str, "pages": int})
        graph.add_node("a", lambda state: {"pages": "three"})

        with self.assertRaises(StateValidationError):
            run(graph, {"file": "a.pdf", "pages": 0})

    def test_node_must_return_dict(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: "oops")

        with self.assertRaises(StateValidationError):
            run(graph, {})

    def test_graph_with_unknown_target_is_rejected(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: None, fallback="missing")

        with self.assertRaises(GraphError):
            run(graph, {})

    def test_duplicate_and_reserved_names_are_rejected(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: None)
        with self.assertRaises(GraphError):
            graph.add_node("a", lambda state: None)
        with self.assertRaises(GraphError):
            graph.add_node(END, lambda state: None)

    def test_node_cannot_have_both_edge_types(self):
        graph = self.make_graph()
        graph.add_node("a", lambda state: None)
        graph.add_edge("a", END)
        with self.assertRaises(GraphError):
            graph.add_conditional_edges("a", lambda state: END)
