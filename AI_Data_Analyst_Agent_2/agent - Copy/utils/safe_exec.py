"""Secure code execution sandbox and query sanitization engine for AI_Data_Analyst_Agent_2.

Provides AST-based inspection, prohibited builtins/imports/system calls blacklisting,
query sanitization, and execution isolation with timeout bounds.
"""

import ast
import concurrent.futures
import re
from typing import Any, Dict, Optional, Set
import pandas as pd
import numpy as np


class SecurityViolationError(Exception):
    """Raised when generated code contains unsafe AST nodes, imports, or attributes."""
    pass


class CodeTimeoutError(TimeoutError):
    """Raised when code execution exceeds the allowed execution time limit."""
    pass


# Prohibited module names that cannot be imported or accessed
BANNED_MODULES: Set[str] = {
    "os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
    "http", "ftplib", "smtplib", "telnetlib", "pty", "commands", "posix",
    "nt", "builtins", "__builtins__", "platform", "ctypes", "threading",
    "multiprocessing", "importlib", "pickle", "marshal", "shelve", "dbm",
    "sqlite3", "webbrowser", "pathlib", "tempfile", "glob", "inspect"
}

# Dangerous built-in function names that cannot be invoked
BANNED_BUILTIN_FUNCS: Set[str] = {
    "eval", "exec", "compile", "open", "input", "__import__", "globals",
    "locals", "vars", "breakpoint", "exit", "quit", "getattr", "setattr",
    "delattr", "hasattr", "isinstance", "issubclass", "memoryview",
    "classmethod", "staticmethod", "super", "help", "execfile", "raw_input"
}

# Dangerous method names and file write/exfiltration attributes
BANNED_ATTRIBUTES: Set[str] = {
    "to_csv", "to_excel", "to_sql", "to_parquet", "to_feather", "to_pickle",
    "to_json", "to_html", "to_stata", "to_clipboard", "read_csv", "read_table",
    "read_excel", "read_sql", "read_parquet", "read_feather", "read_pickle",
    "system", "popen", "spawn"
}

# Whitelist of safe Python builtins permitted inside the sandbox
SAFE_BUILTINS: Dict[str, Any] = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "sorted": sorted,
    "filter": filter,
    "map": map,
    "all": all,
    "any": any,
    "True": True,
    "False": False,
    "None": None,
}


def sanitize_code(code: str) -> str:
    """Sanitize and clean raw LLM code outputs.

    Removes markdown code block formatting (```python ... ```), extraneous whitespace,
    and trailing semicolons.
    """
    if not isinstance(code, str):
        raise ValueError("Input code must be a string")

    cleaned = code.strip()

    # Strip markdown code blocks: ```python ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:python)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Strip redundant leading language identifier
    if cleaned.lower().startswith("python\n"):
        cleaned = cleaned[7:].strip()

    # Strip trailing semicolons
    cleaned = cleaned.rstrip(";")

    return cleaned.strip()


class ASTSecurityInspector(ast.NodeVisitor):
    """AST visitor that validates generated Python code against security policies."""

    def visit_Import(self, node: ast.Import) -> None:
        names = [alias.name for alias in node.names]
        raise SecurityViolationError(f"Import statements are prohibited in sandbox: {names}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        raise SecurityViolationError(f"ImportFrom statements are prohibited in sandbox: {module}")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BANNED_MODULES:
            raise SecurityViolationError(f"Access to prohibited module/identifier '{node.id}' is blocked")
        if node.id in BANNED_BUILTIN_FUNCS:
            raise SecurityViolationError(f"Access to prohibited built-in function '{node.id}' is blocked")
        if node.id.startswith("__"):
            raise SecurityViolationError(f"Dunder identifiers like '{node.id}' are prohibited")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__"):
            raise SecurityViolationError(f"Dunder attribute access '{node.attr}' is prohibited")
        if node.attr in BANNED_ATTRIBUTES:
            raise SecurityViolationError(f"Access to dangerous method/attribute '{node.attr}' is prohibited")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check direct function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in BANNED_BUILTIN_FUNCS or func_name in BANNED_MODULES:
                raise SecurityViolationError(f"Execution of prohibited function '{func_name}' is blocked")
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in BANNED_ATTRIBUTES or attr_name.startswith("__"):
                raise SecurityViolationError(f"Execution of prohibited attribute method '{attr_name}' is blocked")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        raise SecurityViolationError("Global statements are prohibited in sandbox")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise SecurityViolationError("Nonlocal statements are prohibited in sandbox")

    def visit_Delete(self, node: ast.Delete) -> None:
        raise SecurityViolationError("Delete statements are prohibited in sandbox")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        raise SecurityViolationError("Function definitions are prohibited in sandbox query code")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        raise SecurityViolationError("Async function definitions are prohibited in sandbox")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        raise SecurityViolationError("Class definitions are prohibited in sandbox")

    def visit_With(self, node: ast.With) -> None:
        raise SecurityViolationError("With statements are prohibited in sandbox")

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        raise SecurityViolationError("AsyncWith statements are prohibited in sandbox")

    def visit_Try(self, node: ast.Try) -> None:
        raise SecurityViolationError("Try/except blocks are prohibited in sandbox")

    def visit_Raise(self, node: ast.Raise) -> None:
        raise SecurityViolationError("Raise statements are prohibited in sandbox")

    def visit_Yield(self, node: ast.Yield) -> None:
        raise SecurityViolationError("Yield expressions are prohibited in sandbox")

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        raise SecurityViolationError("YieldFrom expressions are prohibited in sandbox")


def validate_code(code: str) -> ast.AST:
    """Parse and inspect Python code using Abstract Syntax Tree (AST) validation.

    Raises:
        SyntaxError: If the code cannot be parsed.
        SecurityViolationError: If unsafe operations, modules, or attributes are detected.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in generated code: {e}") from e

    inspector = ASTSecurityInspector()
    inspector.visit(tree)
    return tree


def _run_in_sandbox(tree: ast.AST, df: Any) -> Any:
    """Internal runner that executes validated AST inside a restricted namespace."""
    safe_globals: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "pd": pd,
        "np": np,
    }
    safe_locals: Dict[str, Any] = {
        "df": df,
    }

    # If code is a single expression, evaluate it directly in eval mode
    if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
        expr_ast = ast.Expression(body=tree.body[0].value)
        compiled = compile(expr_ast, filename="<sandbox>", mode="eval")
        return eval(compiled, safe_globals, safe_locals)

    # Otherwise execute module statements (e.g. result = df['col'].mean())
    compiled = compile(tree, filename="<sandbox>", mode="exec")
    exec(compiled, safe_globals, safe_locals)

    if "result" in safe_locals:
        return safe_locals["result"]

    # If result wasn't assigned, find the last modified local variable
    for key in reversed(list(safe_locals.keys())):
        if key != "df":
            return safe_locals[key]

    return None


def execute_safe_code(code: str, df: Any, timeout: float = 5.0) -> Any:
    """Sanitize, validate, and execute Python code in a secure execution sandbox.

    Args:
        code: The Python code string to execute.
        df: The pandas DataFrame passed to the sandbox.
        timeout: Maximum execution time in seconds (default 5.0).

    Returns:
        The evaluated result of the query.

    Raises:
        SecurityViolationError: If code fails AST validation or attempts prohibited operations.
        CodeTimeoutError: If execution exceeds the allotted timeout.
        Exception: If execution encounters a runtime error.
    """
    if code is None or not str(code).strip():
        raise ValueError("Cannot execute empty or null code")

    sanitized = sanitize_code(code)
    tree = validate_code(sanitized)

    # Execute in a worker thread to enforce timeout bounds
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_in_sandbox, tree, df)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as e:
            raise CodeTimeoutError(f"Code execution exceeded time limit of {timeout}s") from e
        except Exception as e:
            # Re-raise SecurityViolationError directly
            if isinstance(e, SecurityViolationError):
                raise
            raise e
