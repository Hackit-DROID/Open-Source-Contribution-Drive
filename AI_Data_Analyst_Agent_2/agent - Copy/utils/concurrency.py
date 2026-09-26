import functools
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


class TransientTransactionError(Exception):
    pass


class VersionConflictError(TransientTransactionError):
    def __init__(self, key: str, expected: int, actual: int):
        self.key = key
        self.expected = expected
        self.actual = actual
        super().__init__(f"Version conflict on '{key}': expected version {expected}, found {actual}")


class DeadlockError(TransientTransactionError):
    pass


class SerializationFailureError(TransientTransactionError):
    pass


class RetryExhaustedError(Exception):
    def __init__(self, attempts: int, last_error: BaseException):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Transaction aborted after {attempts} attempts: {last_error}")


TRANSIENT_SQLSTATES = {"40001", "40P01"}
TRANSIENT_DRIVER_ERRORS = {"OperationalError", "TransactionRollbackError", "SerializationFailure", "DeadlockDetected"}
TRANSIENT_MESSAGES = ("deadlock", "could not serialize", "serialization failure", "database is locked")


def is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, TransientTransactionError):
        return True
    if getattr(exc, "pgcode", None) in TRANSIENT_SQLSTATES or getattr(exc, "sqlstate", None) in TRANSIENT_SQLSTATES:
        return True
    if type(exc).__name__ in TRANSIENT_DRIVER_ERRORS:
        message = str(exc).lower()
        return any(marker in message for marker in TRANSIENT_MESSAGES)
    return False


@dataclass(frozen=True)
class VersionedEntity:
    key: str
    value: Any
    version: int


class VersionedStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._entities: Dict[str, VersionedEntity] = {}
        self._conflicts = 0

    @property
    def conflicts(self) -> int:
        with self._lock:
            return self._conflicts

    def get(self, key: str) -> Optional[VersionedEntity]:
        with self._lock:
            return self._entities.get(key)

    def version(self, key: str) -> int:
        entity = self.get(key)
        return entity.version if entity else 0

    def put(self, key: str, value: Any) -> VersionedEntity:
        with self._lock:
            current = self._entities.get(key)
            entity = VersionedEntity(key, value, (current.version if current else 0) + 1)
            self._entities[key] = entity
            return entity

    def compare_and_set(self, key: str, expected_version: int, value: Any) -> VersionedEntity:
        with self._lock:
            current = self._entities.get(key)
            actual = current.version if current else 0
            if actual != expected_version:
                self._conflicts += 1
                raise VersionConflictError(key, expected_version, actual)
            entity = VersionedEntity(key, value, actual + 1)
            self._entities[key] = entity
            return entity

    def update(self, key: str, mutate: Callable[[Optional[VersionedEntity]], Any]) -> VersionedEntity:
        snapshot = self.get(key)
        new_value = mutate(snapshot)
        return self.compare_and_set(key, snapshot.version if snapshot else 0, new_value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._entities.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entities.clear()
            self._conflicts = 0


def retry_on_conflict(
    max_attempts: int = 5,
    base_delay: float = 0.005,
    max_delay: float = 0.1,
    jitter: bool = True,
    retry_if: Callable[[BaseException], bool] = is_transient_error,
    sleep: Callable[[float], None] = time.sleep,
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if not retry_if(exc):
                        raise
                    if attempt == max_attempts:
                        raise RetryExhaustedError(attempt, exc) from exc
                    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    sleep(random.uniform(0, delay) if jitter else delay)

        wrapper.max_attempts = max_attempts
        return wrapper

    return decorator
