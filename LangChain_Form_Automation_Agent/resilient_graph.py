"""
Resilient Graph State Machine for LangChain Form Automation Agent (CR-1495).

Provides a lightweight, LangGraph-compatible StateGraph implementation supporting:
- Multi-node graph state execution with sync (invoke) and async (ainvoke)
- Conditional retry edge routing with cyclic node re-execution
- Fallback and recovery node transitions
- Bounded exponential backoff
- State schema validation
- Execution trace and error context preservation
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_type_hints,
)

# Graph Sentinels (matching LangGraph conventions)
START = "__start__"
END = "__end__"


class StateValidationError(Exception):
    """Raised when the graph state violates schema or type constraints."""
    pass


def classify_error(error: Exception) -> str:
    """
    Classify an exception into 'transient' (retryable) or 'fatal' (non-retryable).
    """
    if isinstance(error, (StateValidationError, ValueError, TypeError, KeyError, AttributeError)):
        return "fatal"

    error_str = f"{type(error).__name__} {error}".lower()

    fatal_kws = ["unauthorized", "401", "forbidden", "403", "not found", "404", "invalid argument", "schema"]
    if any(kw in error_str for kw in fatal_kws):
        return "fatal"

    if isinstance(error, (TimeoutError, ConnectionError, ConnectionResetError, ConnectionRefusedError)):
        return "transient"

    transient_kws = ["timeout", "timed out", "rate limit", "429", "too many requests", "connection reset", "503", "service unavailable", "econnreset"]
    if any(kw in error_str for kw in transient_kws):
        return "transient"

    return "fatal"


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
) -> float:
    """Calculate bounded exponential backoff delay."""
    if attempt <= 0:
        return 0.0
    return min(base_delay * (factor ** (attempt - 1)), max_delay)


def execute_backoff(
    attempt: int,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> float:
    """Execute synchronous backoff sleep."""
    delay = calculate_backoff_delay(attempt, base_delay, factor, max_delay)
    if delay > 0 and sleep_fn:
        sleep_fn(delay)
    elif delay > 0 and sleep_fn is None:
        time.sleep(delay)
    return delay


async def execute_backoff_async(
    attempt: int,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 30.0,
    async_sleep_fn: Optional[Callable[[float], Any]] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> float:
    """Execute asynchronous backoff sleep without blocking the event loop."""
    delay = calculate_backoff_delay(attempt, base_delay, factor, max_delay)
    if delay > 0:
        if async_sleep_fn:
            res = async_sleep_fn(delay)
            if inspect.isawaitable(res):
                await res
        elif sleep_fn and sleep_fn != time.sleep:
            sleep_fn(delay)
        else:
            await asyncio.sleep(delay)
    return delay


def _check_type_match(val: Any, expected_type: Any) -> bool:
    if expected_type is Any:
        return True
    origin = getattr(expected_type, "__origin__", None)
    if origin is Union:
        args = getattr(expected_type, "__args__", ())
        return any(_check_type_match(val, a) for a in args)
    check_type = origin if origin is not None else expected_type
    if isinstance(check_type, type):
        return isinstance(val, check_type)
    return True


def validate_state(state: Dict[str, Any], schema: Optional[Union[Type, Dict[str, Type]]]) -> None:
    """Validate state keys and types against schema (TypedDict or dict of types)."""
    if not schema:
        return

    expected_types: Dict[str, Any] = {}
    required_keys: Set[str] = set()

    if isinstance(schema, dict):
        expected_types = schema
        required_keys = set(schema.keys())
    elif hasattr(schema, "__annotations__"):
        expected_types = get_type_hints(schema)
        required_keys = getattr(schema, "__required_keys__", set(expected_types.keys()))
    else:
        return

    for key in required_keys:
        if key not in state:
            raise StateValidationError(f"Missing required state key: '{key}'")

    for key, expected_type in expected_types.items():
        if key in state and state[key] is not None:
            if not _check_type_match(state[key], expected_type):
                raise StateValidationError(
                    f"State key '{key}' expected type {expected_type}, got {type(state[key]).__name__}"
                )


class StateGraph:
    """
    Lightweight, LangGraph-compatible multi-node graph state machine.
    """
    def __init__(self, state_schema: Optional[Union[Type, Dict[str, Type]]] = None):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Tuple[Callable[[Dict[str, Any]], Any], Optional[Dict[str, str]]]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, action: Callable[[Dict[str, Any]], Any]) -> StateGraph:
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists in graph.")
        self.nodes[name] = action
        return self

    def add_edge(self, from_node: str, to_node: str) -> StateGraph:
        if from_node != START and from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' does not exist.")
        if to_node != END and to_node not in self.nodes:
            raise ValueError(f"Destination node '{to_node}' does not exist.")
        self.edges[from_node] = to_node
        return self

    def add_conditional_edges(
        self,
        source: str,
        path_fn: Callable[[Dict[str, Any]], Any],
        path_map: Optional[Dict[str, str]] = None,
    ) -> StateGraph:
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' does not exist.")
        self.conditional_edges[source] = (path_fn, path_map)
        return self

    def set_entry_point(self, name: str) -> StateGraph:
        if name not in self.nodes:
            raise ValueError(f"Entry node '{name}' does not exist.")
        self.entry_point = name
        return self

    def compile(self) -> CompiledGraph:
        if not self.entry_point:
            raise ValueError("StateGraph entry point is not set.")
        return CompiledGraph(self)


class CompiledGraph:
    """Compiled runnable execution engine for StateGraph."""
    def __init__(self, graph: StateGraph):
        self.graph = graph

    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph state machine asynchronously."""
        state = dict(initial_state)
        state.setdefault("trace", [])
        validate_state(state, self.graph.state_schema)

        current_node: Optional[str] = self.graph.entry_point

        while current_node and current_node != END:
            state["trace"].append(current_node)
            node_fn = self.graph.nodes.get(current_node)
            if not node_fn:
                state["status"] = "failed"
                state["error"] = f"Node '{current_node}' not found."
                break

            try:
                if inspect.iscoroutinefunction(node_fn):
                    update = await node_fn(state)
                else:
                    update = node_fn(state)
                    if inspect.isawaitable(update):
                        update = await update

                if isinstance(update, dict):
                    state.update(update)
                validate_state(state, self.graph.state_schema)
            except Exception as exc:
                state["error"] = str(exc)
                state["status"] = "failed"
                return state

            # Route to next node
            if current_node in self.graph.conditional_edges:
                path_fn, path_map = self.graph.conditional_edges[current_node]
                if inspect.iscoroutinefunction(path_fn):
                    route_key = await path_fn(state)
                else:
                    route_key = path_fn(state)
                    if inspect.isawaitable(route_key):
                        route_key = await route_key
                next_node = path_map.get(route_key) if path_map else route_key
            else:
                next_node = self.graph.edges.get(current_node, END)

            current_node = next_node

        if state.get("status") not in ("recovered", "failed"):
            state["status"] = "success"
        return state

    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph state machine synchronously."""
        state = dict(initial_state)
        state.setdefault("trace", [])
        validate_state(state, self.graph.state_schema)

        current_node: Optional[str] = self.graph.entry_point

        while current_node and current_node != END:
            state["trace"].append(current_node)
            node_fn = self.graph.nodes.get(current_node)
            if not node_fn:
                state["status"] = "failed"
                state["error"] = f"Node '{current_node}' not found."
                break

            try:
                update = node_fn(state)
                if inspect.isawaitable(update):
                    update = asyncio.run(update)

                if isinstance(update, dict):
                    state.update(update)
                validate_state(state, self.graph.state_schema)
            except Exception as exc:
                state["error"] = str(exc)
                state["status"] = "failed"
                return state

            if current_node in self.graph.conditional_edges:
                path_fn, path_map = self.graph.conditional_edges[current_node]
                route_key = path_fn(state)
                if inspect.isawaitable(route_key):
                    route_key = asyncio.run(route_key)
                next_node = path_map.get(route_key) if path_map else route_key
            else:
                next_node = self.graph.edges.get(current_node, END)

            current_node = next_node

        if state.get("status") not in ("recovered", "failed"):
            state["status"] = "success"
        return state
