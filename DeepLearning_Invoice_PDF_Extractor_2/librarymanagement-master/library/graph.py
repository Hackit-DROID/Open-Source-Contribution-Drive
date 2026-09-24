import asyncio
import inspect
import random
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

END = "__end__"


class GraphError(Exception):
    pass


class StateValidationError(GraphError):
    pass


class NodeFailedError(GraphError):
    def __init__(self, node, error):
        super().__init__(f"node '{node}' failed: {error}")
        self.node = node
        self.error = error


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    backoff: float = 2.0
    max_delay: float = 8.0
    jitter: float = 0.0
    retry_on: Tuple[type, ...] = (Exception,)

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def delay_for(self, attempt):
        delay = min(self.base_delay * (self.backoff ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay += random.uniform(0, self.jitter)
        return delay

    def should_retry(self, error):
        return isinstance(error, self.retry_on)


@dataclass
class Node:
    name: str
    func: Callable[[Dict[str, Any]], Any]
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    fallback: Optional[str] = None
    timeout: Optional[float] = None


@dataclass
class Step:
    node: str
    status: str
    attempts: int
    error: Optional[str] = None


@dataclass
class RunResult:
    state: Dict[str, Any]
    steps: List[Step]

    @property
    def path(self):
        return [step.node for step in self.steps]

    @property
    def recovered(self):
        return any(step.status == "failed" for step in self.steps)


class StateGraph:
    def __init__(self, schema=None, max_steps=50, sleep=None):
        self.schema = schema or {}
        self.max_steps = max_steps
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, str] = {}
        self.routers: Dict[str, Tuple[Callable, Optional[Dict[Any, str]]]] = {}
        self.entry: Optional[str] = None
        self._sleep: Callable[[float], Awaitable[None]] = sleep or asyncio.sleep

    def add_node(self, name, func, retry=None, fallback=None, timeout=None):
        if name == END:
            raise GraphError(f"'{END}' is reserved")
        if name in self.nodes:
            raise GraphError(f"node '{name}' already exists")
        self.nodes[name] = Node(name, func, retry or RetryPolicy(), fallback, timeout)
        if self.entry is None:
            self.entry = name
        return self

    def add_edge(self, source, target):
        if source in self.routers:
            raise GraphError(f"node '{source}' already has conditional edges")
        self.edges[source] = target
        return self

    def add_conditional_edges(self, source, router, mapping=None):
        if source in self.edges:
            raise GraphError(f"node '{source}' already has a direct edge")
        self.routers[source] = (router, mapping)
        return self

    def set_entry(self, name):
        self.entry = name
        return self

    def validate_graph(self):
        if self.entry not in self.nodes:
            raise GraphError(f"entry node '{self.entry}' is not defined")
        targets = list(self.edges.items())
        targets += [(node.name, node.fallback) for node in self.nodes.values() if node.fallback]
        for _, (_, mapping) in self.routers.items():
            targets += [(None, target) for target in (mapping or {}).values()]
        for source, target in targets:
            if source is not None and source not in self.nodes:
                raise GraphError(f"edge starts at unknown node '{source}'")
            if target != END and target not in self.nodes:
                raise GraphError(f"edge points to unknown node '{target}'")
        for source in self.routers:
            if source not in self.nodes:
                raise GraphError(f"edge starts at unknown node '{source}'")

    def validate_state(self, state):
        if not isinstance(state, dict):
            raise StateValidationError("state must be a dict")
        for key, expected in self.schema.items():
            if key not in state:
                raise StateValidationError(f"missing state key '{key}'")
            if not isinstance(state[key], expected):
                raise StateValidationError(
                    f"state key '{key}' should be {getattr(expected, '__name__', expected)}, "
                    f"got {type(state[key]).__name__}"
                )

    async def run(self, state):
        self.validate_graph()
        state = dict(state)
        self.validate_state(state)
        steps = []
        current = self.entry

        while current != END:
            if len(steps) >= self.max_steps:
                raise GraphError(f"stopped after {self.max_steps} steps, possible loop at '{current}'")
            node = self.nodes[current]
            update, error, attempts = await self._execute(node, state)
            if error is not None:
                steps.append(Step(node.name, "failed", attempts, repr(error)))
                state["errors"] = state.get("errors", []) + [{"node": node.name, "error": repr(error)}]
                if node.fallback is None:
                    raise NodeFailedError(node.name, error) from error
                current = node.fallback
                continue

            if update:
                if not isinstance(update, dict):
                    raise StateValidationError(f"node '{node.name}' must return a dict or None")
                state.update(update)
            self.validate_state(state)
            steps.append(Step(node.name, "ok", attempts))
            current = self._next(node.name, state)

        return RunResult(state, steps)

    async def _execute(self, node, state):
        policy = node.retry
        attempt = 0
        while True:
            attempt += 1
            try:
                return await self._call(node, dict(state)), None, attempt
            except Exception as error:
                if attempt >= policy.max_attempts or not policy.should_retry(error):
                    return None, error, attempt
                await self._sleep(policy.delay_for(attempt))

    async def _call(self, node, state):
        result = node.func(state)
        if inspect.isawaitable(result):
            if node.timeout is not None:
                return await asyncio.wait_for(result, node.timeout)
            return await result
        return result

    def _next(self, source, state):
        if source in self.routers:
            router, mapping = self.routers[source]
            key = router(state)
            if mapping is None:
                target = key
            elif key in mapping:
                target = mapping[key]
            else:
                raise GraphError(f"router for '{source}' returned unknown route '{key}'")
            if target != END and target not in self.nodes:
                raise GraphError(f"router for '{source}' returned unknown node '{target}'")
            return target
        return self.edges.get(source, END)
