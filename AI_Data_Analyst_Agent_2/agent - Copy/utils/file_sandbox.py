import atexit
import os
import shutil
import sys
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from utils.safe_exec import SecurityViolationError

DEFAULT_SCRATCH_ROOT = os.environ.get(
    "SANDBOX_SCRATCH_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch"),
)
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_FILES = 20
SANDBOX_PREFIX = "sandbox-"

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
PATH_MUTATION_EVENTS = {
    "os.remove": 1,
    "os.rmdir": 1,
    "os.mkdir": 1,
    "os.truncate": 1,
    "os.chmod": 1,
    "os.chown": 1,
    "os.utime": 1,
    "os.rename": 2,
    "os.link": 2,
    "os.symlink": 2,
    "shutil.rmtree": 1,
    "shutil.copyfile": 2,
    "shutil.copytree": 2,
    "shutil.move": 2,
    "shutil.make_archive": 1,
    "shutil.unpack_archive": 2,
}


class SandboxViolationError(SecurityViolationError):
    pass


class SandboxQuotaError(SandboxViolationError):
    pass


_active = threading.local()
_hook_lock = threading.Lock()
_hook_installed = False
_live_sandboxes: "set[FileSandbox]" = set()
_live_lock = threading.Lock()


def _real(path: str) -> str:
    return os.path.realpath(os.path.abspath(path))


def _is_within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def _is_write_open(mode: Any, flags: Any) -> bool:
    if isinstance(mode, str) and any(ch in mode for ch in "wax+"):
        return True
    return isinstance(flags, int) and bool(flags & WRITE_FLAGS)


def _audit_hook(event: str, args: tuple) -> None:
    sandbox = getattr(_active, "sandbox", None)
    if sandbox is None:
        return

    if event == "open":
        path = args[0] if args else None
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else None
        if isinstance(path, int) or not _is_write_open(mode, flags):
            return
        sandbox._authorize_write(path)
        return

    count = PATH_MUTATION_EVENTS.get(event)
    if count:
        for path in args[:count]:
            if isinstance(path, (str, bytes, os.PathLike)):
                sandbox._authorize_path(path, event)


def install_audit_hook() -> None:
    global _hook_installed
    with _hook_lock:
        if not _hook_installed:
            sys.addaudithook(_audit_hook)
            _hook_installed = True


def cleanup_stale_sandboxes(root: str = DEFAULT_SCRATCH_ROOT, max_age: float = 3600.0) -> int:
    if not os.path.isdir(root):
        return 0
    removed = 0
    cutoff = time.time() - max_age
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if name.startswith(SANDBOX_PREFIX) and os.path.isdir(path) and os.path.getmtime(path) < cutoff:
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
    return removed


def _cleanup_live_sandboxes() -> None:
    with _live_lock:
        sandboxes = list(_live_sandboxes)
    for sandbox in sandboxes:
        sandbox.cleanup()


atexit.register(_cleanup_live_sandboxes)


class FileSandbox:
    def __init__(self, root: str = DEFAULT_SCRATCH_ROOT, max_bytes: int = DEFAULT_MAX_BYTES,
                 max_files: int = DEFAULT_MAX_FILES):
        install_audit_hook()
        os.makedirs(root, exist_ok=True)
        self.root = _real(root)
        self.max_bytes = max_bytes
        self.max_files = max_files
        self.directory = os.path.join(self.root, f"{SANDBOX_PREFIX}{uuid.uuid4().hex}")
        os.mkdir(self.directory)
        self.directory = _real(self.directory)
        self._written: "set[str]" = set()
        self._lock = threading.Lock()
        self._closed = False
        with _live_lock:
            _live_sandboxes.add(self)

    def __enter__(self) -> "FileSandbox":
        return self

    def __exit__(self, *exc_info) -> None:
        self.cleanup()

    @property
    def closed(self) -> bool:
        return self._closed

    def resolve(self, path: Any) -> str:
        if isinstance(path, bytes):
            path = os.fsdecode(path)
        path = os.fspath(path)
        if not isinstance(path, str) or not path or "\x00" in path:
            raise SandboxViolationError(f"Invalid sandbox path: {path!r}")
        candidate = path if os.path.isabs(path) else os.path.join(self.directory, path)
        resolved = _real(candidate)
        if resolved == self.directory or not _is_within(resolved, self.directory):
            raise SandboxViolationError(f"Path '{path}' is outside the sandbox directory")
        return resolved

    def path(self, name: str) -> str:
        resolved = self.resolve(name)
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        return resolved

    def open(self, file: Any, mode: str = "r", *args, **kwargs):
        if isinstance(file, int):
            raise SandboxViolationError("Opening raw file descriptors is not allowed in the sandbox")
        return open(self.resolve(file), mode, *args, **kwargs)

    def _authorize_path(self, path: Any, event: str) -> str:
        try:
            resolved = _real(os.fsdecode(path) if isinstance(path, bytes) else os.fspath(path))
        except TypeError:
            raise SandboxViolationError(f"Blocked {event} on unsupported path {path!r}")
        if self._closed or not _is_within(resolved, self.directory):
            raise SandboxViolationError(
                f"Blocked {event} on '{path}': file system changes are only allowed inside the sandbox directory"
            )
        return resolved

    def _authorize_write(self, path: Any) -> None:
        resolved = self._authorize_path(path, "write")
        with self._lock:
            if resolved not in self._written and len(self._written) >= self.max_files:
                raise SandboxQuotaError(f"Sandbox file limit of {self.max_files} files exceeded")
            self._written.add(resolved)

    def activate(self) -> None:
        if self._closed:
            raise SandboxViolationError("Sandbox has already been cleaned up")
        _active.sandbox = self

    @staticmethod
    def deactivate() -> None:
        _active.sandbox = None

    def usage(self) -> Dict[str, int]:
        total = count = 0
        for dirpath, _, filenames in os.walk(self.directory):
            for name in filenames:
                full = os.path.join(dirpath, name)
                if not os.path.islink(full):
                    total += os.path.getsize(full)
                    count += 1
        return {"bytes": total, "files": count}

    def enforce_quota(self) -> None:
        usage = self.usage()
        if usage["bytes"] > self.max_bytes:
            raise SandboxQuotaError(
                f"Sandbox storage limit exceeded: {usage['bytes']} bytes written, limit is {self.max_bytes}"
            )
        if usage["files"] > self.max_files:
            raise SandboxQuotaError(f"Sandbox file limit of {self.max_files} files exceeded")

    def list_files(self) -> List[Dict[str, Any]]:
        if self._closed or not os.path.isdir(self.directory):
            return []
        files = []
        for dirpath, _, filenames in os.walk(self.directory):
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                files.append({
                    "name": os.path.relpath(full, self.directory),
                    "size": os.path.getsize(full),
                })
        return sorted(files, key=lambda item: item["name"])

    def cleanup(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        shutil.rmtree(self.directory, ignore_errors=True)
        with _live_lock:
            _live_sandboxes.discard(self)


def current_sandbox() -> Optional[FileSandbox]:
    return getattr(_active, "sandbox", None)
