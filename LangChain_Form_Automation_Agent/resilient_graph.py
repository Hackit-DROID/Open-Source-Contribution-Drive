"""
Resilient Multi-Node Agent Execution Graph Framework (CR-1491).

Provides an agent execution state graph supporting:
- Explicit execution state tracking and schema validation
- Configurable retry policies with bounded exponential backoff
- Precise error classification (transient/retryable vs. fatal/non-retryable)
- Conditional retry and recovery edges
- Fallback/recovery node execution with graceful degradation
- Deterministic termination and execution trace recording
"""

from __future__ import annotations

import time
import inspect
from enum import Enum
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

# Special Graph Sentinels
START = "__start__"
END = "__end__"
RETRY = "__retry__"
RECOVERY = "__recovery__"


class ErrorCategory(str, Enum):
    """Classification of errors for conditional routing."""
    RETRYABLE = "retryable"
    FATAL = "fatal"


class ExecutionStatus(str, Enum):
    """Status of graph or node execution."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    RETRYING = "retrying"
    RECOVERED = "recovered"
    DEGRADED = "degraded"
    FAILED = "failed"


class GraphError(Exception):
    """Base exception for graph execution errors."""
    pass


class StateValidationError(GraphError):
    """Raised when the state fails schema or type validation."""
    pass


class TransientNodeError(GraphError):
    """Explicitly retryable transient failure (timeout, network, rate limit)."""
    pass


class FatalNodeError(GraphError):
    """Explicitly fatal non-retryable failure (invalid data, schema violation)."""
    pass


class RetryExhaustedError(GraphError):
    """Raised when maximum retry attempts for a node are exhausted."""
    def __init__(self, node: str, attempts: int, last_error: Optional[Exception] = None):
        super().__init__(f"Node '{node}' exhausted maximum retry attempts ({attempts}): {last_error}")
        self.node = node
        self.attempts = attempts
        self.last_error = last_error


def default_error_classifier(error: Exception) -> ErrorCategory:
    """
    Classify an exception into RETRYABLE or FATAL.
    
    Transient failures include network timeouts, connection resets, rate limits (429),
    and temporary provider unavailability (503).
    Fatal failures include value/type/key errors, syntax/validation errors, and
    authorization errors (401/403).
    """
    if isinstance(error, FatalNodeError):
        return ErrorCategory.FATAL
    if isinstance(error, (StateValidationError, ValueError, TypeError, KeyError, AttributeError)):
        return ErrorCategory.FATAL
    if isinstance(error, TransientNodeError):
        return ErrorCategory.RETRYABLE
    if isinstance(error, (TimeoutError, ConnectionError, ConnectionResetError, ConnectionRefusedError)):
        return ErrorCategory.RETRYABLE

    # Inspect exception message and class name for common transient patterns
    error_name = type(error).__name__.lower()
    error_msg = str(error).lower()

    retryable_keywords = ["timeout", "timed out", "rate limit", "429", "too many requests", "connection reset", "503", "service unavailable", "econnreset"]
    for kw in retryable_keywords:
        if kw in error_name or kw in error_msg:
            return ErrorCategory.RETRYABLE

    fatal_keywords = ["unauthorized", "401", "forbidden", "403", "not found", "404", "invalid argument", "schema"]
    for kw in fatal_keywords:
        if kw in error_name or kw in error_msg:
            return ErrorCategory.FATAL

    # Default conservative stance: if not explicitly transient, treat as fatal to prevent loops
    return ErrorCategory.FATAL


classify_error = default_error_classifier


class RetryPolicy:
    """
    Bounded exponential backoff policy for resilient node execution.
    """
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 30.0,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if factor < 1.0:
            raise ValueError("factor must be >= 1.0")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.factor = factor
        self.max_delay = max_delay
        self.sleep_fn = sleep_fn or time.sleep

    def calculate_delay(self, attempt: int) -> float:
        """Calculate bounded exponential backoff delay: min(base * (factor ** attempt), max_delay)."""
        if attempt <= 0:
            return 0.0
        # attempt 1 uses factor^0 = base_delay, attempt 2 uses base * factor, etc.
        raw_delay = self.base_delay * (self.factor ** (attempt - 1))
        return min(raw_delay, self.max_delay)

    def execute_backoff(self, attempt: int) -> float:
        """Calculates backoff and executes sleep function, returning sleep duration."""
        delay = self.calculate_delay(attempt)
        if delay > 0 and self.sleep_fn:
            self.sleep_fn(delay)
        return delay


class AgentState(dict):
    """
    Explicit execution state dictionary for multi-node graph traversal.
    
    Provides key-value access, execution metadata tracking,
    schema validation, and execution trace recording.
    """
    def __init__(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        schema: Optional[Union[Type, Dict[str, Type]]] = None,
    ):
        super().__init__()
        self._schema = schema
        self.status: ExecutionStatus = ExecutionStatus.IDLE
        self.current_node: Optional[str] = None
        self.retry_counts: Dict[str, int] = {}
        self.last_error: Optional[str] = None
        self.last_exception: Optional[Exception] = None
        self.error_classification: Optional[ErrorCategory] = None
        self.recovery_status: str = "none"
        self.execution_trace: List[str] = []

        if initial_data:
            self.update(initial_data)

    def record_step(self, step_name: str) -> None:
        """Record step in the execution trace."""
        self.execution_trace.append(step_name)

    def validate(self, schema: Optional[Union[Type, Dict[str, Type]]] = None) -> None:
        """
        Validate state keys and types against schema (TypedDict, dict of types, or dataclass).
        """
        target_schema = schema or self._schema
        if not target_schema:
            return

        expected_types: Dict[str, Any] = {}
        required_keys: Set[str] = set()

        if isinstance(target_schema, dict):
            expected_types = target_schema
            required_keys = set(target_schema.keys())
        elif hasattr(target_schema, "__annotations__"):
            expected_types = get_type_hints(target_schema)
            # TypedDict required keys detection
            required_keys = getattr(target_schema, "__required_keys__", set(expected_types.keys()))
        else:
            return

        # Check required keys
        for key in required_keys:
            if key not in self:
                raise StateValidationError(f"Missing required state key: '{key}'")

        # Check types for present keys
        for key, expected_type in expected_types.items():
            if key in self and self[key] is not None:
                # Handle typing origin if any
                origin = getattr(expected_type, "__origin__", None)
                check_type = origin if origin is not None else expected_type
                if isinstance(check_type, type) and not isinstance(self[key], check_type):
                    raise StateValidationError(
                        f"State key '{key}' expected type {check_type.__name__}, got {type(self[key]).__name__}"
                    )

    def snapshot(self) -> Dict[str, Any]:
        """Return a copy of the accumulated data payload."""
        return dict(self)


class NodeDefinition:
    """Represents a node in the state graph."""
    def __init__(
        self,
        name: str,
        func: Callable[[Union[Dict[str, Any], AgentState]], Any],
        retry_policy: Optional[RetryPolicy] = None,
        fallback_handler: Optional[Callable[[AgentState, Exception], Any]] = None,
        error_classifier: Optional[Callable[[Exception], ErrorCategory]] = None,
    ):
        self.name = name
        self.func = func
        self.retry_policy = retry_policy or RetryPolicy(max_retries=0)
        self.fallback_handler = fallback_handler
        self.error_classifier = error_classifier or default_error_classifier


class ResilientStateGraph:
    """
    A multi-node state graph implementing resilient execution:
    - Conditional retry edges with exponential backoff
    - Automatic error classification
    - Fallback and recovery node transitions
    - State validation
    - Deterministic execution trace
    """
    def __init__(
        self,
        state_schema: Optional[Union[Type, Dict[str, Type]]] = None,
        default_retry_policy: Optional[RetryPolicy] = None,
        default_error_classifier: Optional[Callable[[Exception], ErrorCategory]] = None,
    ):
        self.state_schema = state_schema
        self.default_retry_policy = default_retry_policy or RetryPolicy(max_retries=3, base_delay=0.1)
        self.error_classifier = default_error_classifier or default_error_classifier
        self.nodes: Dict[str, NodeDefinition] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Tuple[Callable[[AgentState], str], Dict[str, str]]] = {}
        self.entry_point: Optional[str] = None
        self.recovery_node_name: Optional[str] = None

    def add_node(
        self,
        name: str,
        action: Callable[[Any], Any],
        retry_policy: Optional[RetryPolicy] = None,
        fallback_handler: Optional[Callable[[AgentState, Exception], Any]] = None,
        error_classifier: Optional[Callable[[Exception], ErrorCategory]] = None,
    ) -> ResilientStateGraph:
        """Register a node with optional custom retry policy and fallback handler."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists in graph.")
        node_def = NodeDefinition(
            name=name,
            func=action,
            retry_policy=retry_policy or self.default_retry_policy,
            fallback_handler=fallback_handler,
            error_classifier=error_classifier or self.error_classifier,
        )
        self.nodes[name] = node_def
        return self

    def add_edge(self, from_node: str, to_node: str) -> ResilientStateGraph:
        """Add a deterministic transition edge between two nodes."""
        if from_node != START and from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' does not exist in graph.")
        if to_node != END and to_node != RECOVERY and to_node not in self.nodes:
            raise ValueError(f"Destination node '{to_node}' does not exist in graph.")
        self.edges[from_node] = to_node
        return self

    def add_conditional_edges(
        self,
        source: str,
        path_fn: Callable[[AgentState], str],
        path_map: Dict[str, str],
    ) -> ResilientStateGraph:
        """
        Add conditional edges routed by path_fn returning a key in path_map.
        """
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' does not exist in graph.")
        self.conditional_edges[source] = (path_fn, path_map)
        return self

    def set_entry_point(self, name: str) -> ResilientStateGraph:
        """Set the starting node of the graph."""
        if name not in self.nodes:
            raise ValueError(f"Entry node '{name}' does not exist in graph.")
        self.entry_point = name
        return self

    def set_recovery_node(
        self,
        name: str,
        recovery_func: Optional[Callable[[AgentState], Any]] = None,
    ) -> ResilientStateGraph:
        """Set or create a dedicated recovery/fallback node."""
        if recovery_func is not None:
            self.add_node(name, recovery_func, retry_policy=RetryPolicy(max_retries=0))
        elif name not in self.nodes:
            raise ValueError(f"Recovery node '{name}' must exist if no function is provided.")
        self.recovery_node_name = name
        return self

    def compile(self) -> CompiledResilientGraph:
        """Compile the state graph into an executable runner."""
        if not self.entry_point:
            raise ValueError("StateGraph entry point is not set.")
        return CompiledResilientGraph(self)


class CompiledResilientGraph:
    """Compiled runnable execution engine for ResilientStateGraph."""

    def __init__(self, graph: ResilientStateGraph):
        self.graph = graph

    def invoke(
        self,
        initial_state: Union[Dict[str, Any], AgentState],
        config: Optional[Dict[str, Any]] = None,
    ) -> AgentState:
        """
        Execute the resilient state graph.
        
        Handles:
        - State schema validation
        - Node execution
        - Conditional retry transitions on retryable failures with exponential backoff
        - Fallback recovery routing on fatal errors or retry exhaustion
        - Clean termination and execution trace collection
        """
        state = (
            initial_state
            if isinstance(initial_state, AgentState)
            else AgentState(initial_state, schema=self.graph.state_schema)
        )
        state.status = ExecutionStatus.RUNNING

        # Initial state schema validation
        try:
            state.validate()
        except StateValidationError as exc:
            state.status = ExecutionStatus.FAILED
            state.last_error = str(exc)
            state.last_exception = exc
            state.error_classification = ErrorCategory.FATAL
            state.record_step("validation_error")
            raise

        current_node_name: Optional[str] = self.graph.entry_point

        while current_node_name and current_node_name != END:
            state.current_node = current_node_name
            state.record_step(current_node_name)

            node_def = self.graph.nodes.get(current_node_name)
            if not node_def:
                state.status = ExecutionStatus.FAILED
                state.last_error = f"Node '{current_node_name}' not found in graph."
                break

            success = False
            while not success:
                try:
                    # Execute node function
                    result = node_def.func(state)

                    # Merge result into state if returned a dict
                    if isinstance(result, dict):
                        state.update(result)
                    elif isinstance(result, AgentState):
                        state.update(result)

                    # Validate updated state
                    state.validate()

                    success = True
                    state.last_error = None
                    state.last_exception = None
                    state.error_classification = None

                except Exception as exc:
                    state.last_error = str(exc)
                    state.last_exception = exc

                    # Classify error
                    classification = node_def.error_classifier(exc)
                    state.error_classification = classification

                    # Check retry policy
                    policy = node_def.retry_policy
                    current_retries = state.retry_counts.get(current_node_name, 0)

                    if classification == ErrorCategory.RETRYABLE and current_retries < policy.max_retries:
                        # Conditional retry path
                        new_attempt = current_retries + 1
                        state.retry_counts[current_node_name] = new_attempt
                        state.record_step(f"retry:{current_node_name}:{new_attempt}")
                        state.status = ExecutionStatus.RETRYING

                        # Exponential backoff
                        policy.execute_backoff(new_attempt)
                        # Loop continues to retry current_node_name
                        state.record_step(current_node_name)
                        continue

                    # Failure routing: retry exhausted or fatal error
                    if classification == ErrorCategory.RETRYABLE:
                        state.record_step(f"exhausted:{current_node_name}")
                    else:
                        state.record_step(f"fatal:{current_node_name}")

                    # Attempt node fallback handler if present
                    handled_by_fallback = False
                    if node_def.fallback_handler:
                        state.record_step(f"fallback:{current_node_name}")
                        try:
                            fallback_result = node_def.fallback_handler(state, exc)
                            if isinstance(fallback_result, dict):
                                state.update(fallback_result)
                            state.recovery_status = "recovered"
                            state.status = ExecutionStatus.RECOVERED
                            handled_by_fallback = True
                        except Exception as fb_exc:
                            # Recovery itself failed: safe containment without crashing
                            state.record_step(f"fallback_failed:{current_node_name}")
                            state.recovery_status = "failed"
                            state.status = ExecutionStatus.FAILED
                            state.last_error = f"Fallback error: {fb_exc}"
                            state.last_exception = fb_exc
                            return state

                    if handled_by_fallback:
                        # Fallback succeeded: determine next step
                        success = True
                        break

                    # Route to global recovery node if defined
                    if self.graph.recovery_node_name:
                        current_node_name = self.graph.recovery_node_name
                        break
                    else:
                        # Unrecoverable termination
                        state.status = ExecutionStatus.FAILED
                        state.recovery_status = "failed"
                        return state

            # Route to next node
            if not success:
                # Routed to recovery node
                continue

            # Determine next node via conditional edges or standard edges
            if current_node_name in self.graph.conditional_edges:
                path_fn, path_map = self.graph.conditional_edges[current_node_name]
                route_key = path_fn(state)
                next_node = path_map.get(route_key)
                if not next_node:
                    state.status = ExecutionStatus.FAILED
                    state.last_error = f"Conditional route key '{route_key}' not mapped."
                    return state
                current_node_name = next_node
            elif current_node_name in self.graph.edges:
                current_node_name = self.graph.edges[current_node_name]
            else:
                # Default end of chain
                current_node_name = END

        if state.status not in (ExecutionStatus.RECOVERED, ExecutionStatus.DEGRADED, ExecutionStatus.FAILED):
            state.status = ExecutionStatus.SUCCESS

        return state
