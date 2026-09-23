#!/usr/bin/env python
"""Django's command-line utility for administrative tasks with Asynchronous Multi-Agent Graph State Machine."""
import asyncio
from dataclasses import dataclass, field
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State Schema & Data Models
# ---------------------------------------------------------------------------

class GraphStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FALLBACK_SUCCESS = "FALLBACK_SUCCESS"
    FAILED = "FAILED"


@dataclass
class AgentGraphState:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_data: Dict[str, Any] = field(default_factory=dict)
    current_node: str = "START"
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    node_history: List[Dict[str, Any]] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    target_retry_node: Optional[str] = None
    max_retries: int = 3
    initial_delay: float = 0.05
    backoff_factor: float = 2.0
    status: str = GraphStatus.PENDING
    fallback_triggered: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateSchema:
    """Validator class ensuring state schema invariants."""

    @staticmethod
    def validate(state: AgentGraphState) -> bool:
        if not isinstance(state.task_id, str) or not state.task_id.strip():
            raise ValueError("StateSchema validation error: task_id must be a non-empty string.")
        if not isinstance(state.input_data, dict):
            raise ValueError("StateSchema validation error: input_data must be a dictionary.")
        if not isinstance(state.extracted_data, dict):
            raise ValueError("StateSchema validation error: extracted_data must be a dictionary.")
        if not isinstance(state.errors, list):
            raise ValueError("StateSchema validation error: errors must be a list.")
        if not isinstance(state.node_history, list):
            raise ValueError("StateSchema validation error: node_history must be a list.")
        if not isinstance(state.retry_counts, dict):
            raise ValueError("StateSchema validation error: retry_counts must be a dictionary.")
        if not isinstance(state.max_retries, int) or state.max_retries < 1:
            raise ValueError("StateSchema validation error: max_retries must be an integer >= 1.")
        if state.status not in {
            GraphStatus.PENDING,
            GraphStatus.RUNNING,
            GraphStatus.SUCCESS,
            GraphStatus.FALLBACK_SUCCESS,
            GraphStatus.FAILED,
        }:
            raise ValueError(f"StateSchema validation error: invalid status '{state.status}'.")
        return True


# ---------------------------------------------------------------------------
# Graph Nodes Definition
# ---------------------------------------------------------------------------

class GraphNode:
    """Base graph node interface."""

    def __init__(self, name: str):
        self.name = name

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        """Executes node logic and returns (updated_state, next_node_name_or_signal)."""
        raise NotImplementedError


class PrimaryExtractorNode(GraphNode):
    """Primary LLM / Invoice extraction agent node."""

    def __init__(self, extractor_fn: Optional[Callable[[Dict[str, Any]], Any]] = None):
        super().__init__("PRIMARY_EXTRACTOR")
        self.extractor_fn = extractor_fn

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        state.current_node = self.name
        try:
            if self.extractor_fn:
                if asyncio.iscoroutinefunction(self.extractor_fn):
                    result = await self.extractor_fn(state.input_data)
                else:
                    result = self.extractor_fn(state.input_data)
            else:
                # Default extraction simulation
                pdf_content = state.input_data.get("pdf_content", "")
                if state.input_data.get("simulated_primary_error"):
                    raise RuntimeError(state.input_data.get("simulated_primary_error"))
                result = {
                    "invoice_id": state.input_data.get("invoice_id", "INV-9999"),
                    "vendor": state.input_data.get("vendor", "Acme Logistics"),
                    "total_amount": state.input_data.get("total_amount", 1250.50),
                    "line_items": state.input_data.get("line_items", [{"desc": "Freight Service", "qty": 1}]),
                    "confidence_score": state.input_data.get("confidence_score", 0.95),
                    "extraction_method": "Primary_LLM_Node",
                }

            state.extracted_data = result
            return state, "VALIDATOR"
        except Exception as exc:
            error_record = {
                "node": self.name,
                "error": str(exc),
                "timestamp": time.time(),
            }
            state.errors.append(error_record)
            current_retries = state.retry_counts.get(self.name, 0)
            if current_retries < state.max_retries:
                state.target_retry_node = self.name
                return state, "ERROR_RECOVERY"
            else:
                return state, "FALLBACK_EXTRACTOR"


class ValidatorNode(GraphNode):
    """Validation node checking invoice schema completeness."""

    def __init__(self, validator_fn: Optional[Callable[[Dict[str, Any]], bool]] = None):
        super().__init__("VALIDATOR")
        self.validator_fn = validator_fn

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        state.current_node = self.name
        try:
            extracted = state.extracted_data
            if self.validator_fn:
                if asyncio.iscoroutinefunction(self.validator_fn):
                    is_valid = await self.validator_fn(extracted)
                else:
                    is_valid = self.validator_fn(extracted)
                if not is_valid:
                    raise ValueError("Validator callback returned False.")
            else:
                # Default validation invariants
                required_keys = ["invoice_id", "total_amount", "vendor"]
                missing = [k for k in required_keys if k not in extracted or extracted[k] is None]
                if missing:
                    raise ValueError(f"Extracted payload missing required fields: {missing}")
                if extracted.get("confidence_score", 1.0) < 0.5:
                    raise ValueError("Confidence score below threshold (0.5).")

            return state, "OUTPUT_FORMATTER"
        except Exception as exc:
            error_record = {
                "node": self.name,
                "error": str(exc),
                "timestamp": time.time(),
            }
            state.errors.append(error_record)
            current_retries = state.retry_counts.get(self.name, 0)
            if current_retries < state.max_retries:
                state.target_retry_node = self.name
                return state, "ERROR_RECOVERY"
            else:
                return state, "FALLBACK_EXTRACTOR"


class ErrorRecoveryNode(GraphNode):
    """Error recovery node implementing exponential backoff retry policies."""

    def __init__(self):
        super().__init__("ERROR_RECOVERY")

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        state.current_node = self.name
        target_node = state.target_retry_node or "PRIMARY_EXTRACTOR"
        current_retries = state.retry_counts.get(target_node, 0)
        
        # Exponential backoff calculation
        delay = state.initial_delay * (state.backoff_factor ** current_retries)
        await asyncio.sleep(delay)
        
        state.retry_counts[target_node] = current_retries + 1
        state.target_retry_node = None
        
        recovery_log = {
            "node": self.name,
            "target_node": target_node,
            "attempt": current_retries + 1,
            "backoff_delay": delay,
            "timestamp": time.time(),
        }
        state.node_history.append(recovery_log)
        return state, target_node


class FallbackExtractorNode(GraphNode):
    """Fallback recovery node triggered when primary retries fail."""

    def __init__(self, fallback_fn: Optional[Callable[[Dict[str, Any]], Any]] = None):
        super().__init__("FALLBACK_EXTRACTOR")
        self.fallback_fn = fallback_fn

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        state.current_node = self.name
        state.fallback_triggered = True
        try:
            if self.fallback_fn:
                if asyncio.iscoroutinefunction(self.fallback_fn):
                    fallback_result = await self.fallback_fn(state.input_data)
                else:
                    fallback_result = self.fallback_fn(state.input_data)
            else:
                fallback_result = {
                    "invoice_id": state.input_data.get("invoice_id", "INV-FALLBACK"),
                    "vendor": state.input_data.get("vendor", "Unknown Vendor"),
                    "total_amount": state.input_data.get("total_amount", 0.0),
                    "confidence_score": 0.50,
                    "extraction_method": "Fallback_RuleEngine_Node",
                    "note": "Recovered via FallbackExtractorNode after primary node failure.",
                }
            state.extracted_data = fallback_result
            state.status = GraphStatus.FALLBACK_SUCCESS
            return state, "OUTPUT_FORMATTER"
        except Exception as exc:
            state.errors.append({
                "node": self.name,
                "error": f"Fallback extraction failed: {str(exc)}",
                "timestamp": time.time(),
            })
            state.status = GraphStatus.FAILED
            return state, "END"


class OutputFormatterNode(GraphNode):
    """Final node formatting state graph payload."""

    def __init__(self):
        super().__init__("OUTPUT_FORMATTER")

    async def execute(self, state: AgentGraphState) -> Tuple[AgentGraphState, str]:
        state.current_node = self.name
        state.extracted_data["_metadata"] = {
            "task_id": state.task_id,
            "fallback_triggered": state.fallback_triggered,
            "total_errors": len(state.errors),
            "total_retries": sum(state.retry_counts.values()),
            "status": state.status if state.status != GraphStatus.PENDING else GraphStatus.SUCCESS,
        }
        if state.status not in {GraphStatus.FALLBACK_SUCCESS, GraphStatus.FAILED}:
            state.status = GraphStatus.SUCCESS
        return state, "END"


# ---------------------------------------------------------------------------
# Asynchronous State Machine Controller
# ---------------------------------------------------------------------------

class AsyncAgentGraphStateMachine:
    """Resilient Multi-Agent Graph State Machine with Fallback Routing."""

    def __init__(
        self,
        primary_extractor_fn: Optional[Callable] = None,
        validator_fn: Optional[Callable] = None,
        fallback_extractor_fn: Optional[Callable] = None,
    ):
        self.nodes: Dict[str, GraphNode] = {
            "PRIMARY_EXTRACTOR": PrimaryExtractorNode(primary_extractor_fn),
            "VALIDATOR": ValidatorNode(validator_fn),
            "ERROR_RECOVERY": ErrorRecoveryNode(),
            "FALLBACK_EXTRACTOR": FallbackExtractorNode(fallback_extractor_fn),
            "OUTPUT_FORMATTER": OutputFormatterNode(),
        }

    async def run(self, initial_state: AgentGraphState) -> AgentGraphState:
        """Executes state graph traversal asynchronously until reaching END state."""
        state = initial_state
        state.status = GraphStatus.RUNNING
        StateSchema.validate(state)

        next_node_name = "PRIMARY_EXTRACTOR"
        max_loop_guard = 100
        step_count = 0

        while next_node_name != "END" and step_count < max_loop_guard:
            step_count += 1
            if next_node_name not in self.nodes:
                state.errors.append({
                    "node": next_node_name,
                    "error": f"Unknown graph node transition target: '{next_node_name}'.",
                    "timestamp": time.time(),
                })
                state.status = GraphStatus.FAILED
                break

            node = self.nodes[next_node_name]
            step_log = {
                "step": step_count,
                "node": node.name,
                "timestamp": time.time(),
            }
            state.node_history.append(step_log)

            try:
                state, next_node_name = await node.execute(state)
                StateSchema.validate(state)
            except Exception as fatal_exc:
                logger.error(f"Fatal error executing graph node {node.name}: {fatal_exc}")
                state.errors.append({
                    "node": node.name,
                    "error": f"Fatal unhandled node exception: {str(fatal_exc)}",
                    "timestamp": time.time(),
                })
                # Trigger fallback route if not already in fallback
                if next_node_name != "FALLBACK_EXTRACTOR" and not state.fallback_triggered:
                    next_node_name = "FALLBACK_EXTRACTOR"
                else:
                    state.status = GraphStatus.FAILED
                    break

        if step_count >= max_loop_guard:
            state.status = GraphStatus.FAILED
            state.errors.append({
                "node": "GRAPH_LOOP_GUARD",
                "error": "State machine execution exceeded maximum loop guard limit.",
                "timestamp": time.time(),
            })

        return state


def execute_async_agent_graph(
    input_data: Dict[str, Any],
    max_retries: int = 3,
    initial_delay: float = 0.01,
    backoff_factor: float = 2.0,
    primary_extractor_fn: Optional[Callable] = None,
    validator_fn: Optional[Callable] = None,
    fallback_extractor_fn: Optional[Callable] = None,
) -> AgentGraphState:
    """Synchronous wrapper function to execute the async agent state graph."""
    state = AgentGraphState(
        input_data=input_data,
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
    )
    graph = AsyncAgentGraphStateMachine(
        primary_extractor_fn=primary_extractor_fn,
        validator_fn=validator_fn,
        fallback_extractor_fn=fallback_extractor_fn,
    )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new event loop if running inside an existing loop context
            import nest_asyncio  # type: ignore
            nest_asyncio.apply()
            return loop.run_until_complete(graph.run(state))
        else:
            return loop.run_until_complete(graph.run(state))
    except RuntimeError:
        return asyncio.run(graph.run(state))


# ---------------------------------------------------------------------------
# Django Main Entrypoint
# ---------------------------------------------------------------------------

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librarymanagement.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
