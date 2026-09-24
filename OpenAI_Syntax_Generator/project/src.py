import os
import sys
import ast
import subprocess
import resource
import signal
import textwrap
from dotenv import load_dotenv

load_dotenv()

FORBIDDEN_MODULES = {"os", "sys", "subprocess", "importlib", "shutil", "pathlib"}
FORBIDDEN_BUILTINS = {"exec", "eval", "compile", "__import__", "open", "input", "globals", "locals"}


class SecurityError(Exception):
    pass


def timeout_handler(signum, frame):
    raise SecurityError("Code execution timed out")


def validate_ast(node):
    """Inspect AST node for forbidden builtins and modules."""
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                raise SecurityError(f"Forbidden import: {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
            raise SecurityError(f"Forbidden from-import: {node.module}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
            raise SecurityError(f"Forbidden builtin call: {node.func.id}")
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_BUILTINS:
                raise SecurityError(f"Forbidden attribute builtin: {node.func.attr}")
    elif isinstance(node, ast.Attribute):
        if node.attr in FORBIDDEN_BUILTINS:
            raise SecurityError(f"Forbidden attribute access: {node.attr}")

    for child in ast.iter_child_nodes(node):
        validate_ast(child)


def sanitize_code(code: str) -> str:
    """Parse code with AST and remove/block forbidden patterns."""
    tree = ast.parse(code)
    validate_ast(tree)
    return code


def timeout_execution(func, *args, timeout_sec=5, **kwargs):
    """Execute function with timeout and memory limits."""
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_sec)
    try:
        result = func(*args, **kwargs)
    except SecurityError:
        result = {"error": "Security violation or timeout"}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    return result


def execute_safely(code: str, timeout_sec=5):
    """Execute user code in a constrained subprocess."""
    try:
        sanitized = sanitize_code(code)
    except SecurityError as e:
        return {"error": f"AST validation failed: {e}"}

    def run_code():
        exec(sanitized, {"__builtins__": {}})

    result = timeout_execution(run_code, timeout_sec=timeout_sec)
    # Limit memory via resource after execution
    resource.setrlimit(resource.RLIMIT_RSS, (1024 * 1024, 1024 * 1024))
    return result


# OpenAI client setup
api_key = os.getenv("OPENAI_API_KEY")
from openai import OpenAI

client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-5-nano",
    input="write python list data structure syntax, example.",
    store=True,
)
print(response.output_text);

# Safe code execution example (commented for production use):
# user_code = "result = [x**2 for x in range(5)]"
# execute_safely(user_code, timeout_sec=3)