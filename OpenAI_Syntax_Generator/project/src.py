import ast
import json
import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Security Exception
# ---------------------------------------------------------------------------

class SecurityValidationError(Exception):
    """Exception raised when AST inspection or query sanitization fails security validation."""
    pass


# ---------------------------------------------------------------------------
# AST Security Inspector
# ---------------------------------------------------------------------------

class ASTSecurityInspector(ast.NodeVisitor):
    """AST Inspector enforcing code isolation and blocking prohibited modules/builtins/attributes."""

    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'ctypes', 'threading',
        'multiprocessing', 'builtins', 'importlib', 'pickle', 'pathlib', 'signal',
        'tempfile', 'urllib', 'requests', 'http', 'ftplib', 'code', 'pty', 'platform'
    }

    FORBIDDEN_BUILTINS = {
        'eval', 'exec', 'open', '__import__', 'compile', 'globals', 'locals',
        'getattr', 'setattr', 'delattr', 'breakpoint', 'system', 'popen', 'file',
        'input', 'raw_input', 'memoryview'
    }

    FORBIDDEN_ATTRIBUTES = {
        '__subclasses__', '__globals__', '__code__', '__mro__', '__bases__',
        '__builtins__', '__dict__', '__class__', 'func_globals', 'gi_frame',
        'f_globals', 'f_locals', 'f_builtins', 'co_code', 'co_consts'
    }

    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in self.FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import module detected: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in self.FORBIDDEN_MODULES:
                self.violations.append(f"Forbidden import from module detected: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_BUILTINS:
                self.violations.append(f"Forbidden builtin function call detected: '{node.func.id}()'")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.FORBIDDEN_BUILTINS:
                self.violations.append(f"Forbidden builtin attribute call detected: '.{node.func.attr}()'")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in self.FORBIDDEN_ATTRIBUTES:
            self.violations.append(f"Forbidden dangerous attribute access detected: '.{node.attr}'")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id in self.FORBIDDEN_BUILTINS:
            self.violations.append(f"Forbidden identifier access detected: '{node.id}'")
        self.generic_visit(node)

    @classmethod
    def inspect(cls, code_str: str) -> bool:
        """Parses python code AST and raises SecurityValidationError if forbidden nodes exist."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as syn_err:
            raise SecurityValidationError(f"Invalid Python syntax: {syn_err}") from syn_err

        visitor = cls()
        visitor.visit(tree)

        if visitor.violations:
            violation_summary = "; ".join(visitor.violations)
            raise SecurityValidationError(f"Security validation blocked code: {violation_summary}")

        return True


# ---------------------------------------------------------------------------
# SQL Query Sanitizer
# ---------------------------------------------------------------------------

class SQLQuerySanitizer:
    """Sanitizer for database queries enforcing read-only query isolation."""

    FORBIDDEN_SQL_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'UPDATE', 'INSERT', 'CREATE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'VACUUM', 'RENAME', 'ATTACH', 'DETACH'
    }

    COMMENT_PATTERNS = [
        re.compile(r'--'),
        re.compile(r'/\*.*?\*/', re.DOTALL),
        re.compile(r';'),
    ]

    @classmethod
    def sanitize(cls, sql_query: str) -> str:
        """Sanitizes SQL query and ensures strict read-only execution."""
        clean_query = sql_query.strip()
        if not clean_query:
            raise SecurityValidationError("Empty SQL query payload.")

        # Check comment injection or multiple statement delimiters
        for pattern in cls.COMMENT_PATTERNS:
            if pattern.search(clean_query):
                raise SecurityValidationError("Forbidden SQL comment or multi-statement delimiter detected.")

        # Tokenize words for keyword checking
        normalized = re.sub(r'\s+', ' ', clean_query).upper()
        words = set(re.findall(r'\b[A-Z_]+\b', normalized))

        forbidden_found = words.intersection(cls.FORBIDDEN_SQL_KEYWORDS)
        if forbidden_found:
            raise SecurityValidationError(f"Forbidden DDL/DML SQL command detected: {forbidden_found}")

        # Enforce Read-Only Isolation (Must start with SELECT or WITH)
        if not (normalized.startswith("SELECT ") or normalized.startswith("WITH ")):
            raise SecurityValidationError("Query isolation failure: Only read-only SELECT or WITH statements are allowed.")

        return clean_query


# ---------------------------------------------------------------------------
# Secure Sandbox Executor
# ---------------------------------------------------------------------------

class SecureSandboxExecutor:
    """Multi-layered isolation sandbox executing Python code in timed subprocesses."""

    @staticmethod
    def execute_python(code_str: str, context_vars: Optional[Dict[str, Any]] = None, timeout: float = 2.0) -> Dict[str, Any]:
        """Inspects code with ASTSecurityInspector and executes in a timed subprocess sandbox."""
        # 1. AST Inspection Phase
        ASTSecurityInspector.inspect(code_str)

        # 2. Subprocess Execution Phase
        runner_script = f"""
import sys, json

context_payload = {json.dumps(context_vars or {})}
allowed_globals = {{
    'abs': abs, 'min': min, 'max': max, 'sum': sum, 'len': len,
    'range': range, 'list': list, 'dict': dict, 'set': set,
    'tuple': tuple, 'str': str, 'int': int, 'float': float,
    'bool': bool, 'print': print
}}

try:
    import pandas as pd
    allowed_globals['pd'] = pd
except ImportError:
    pass

try:
    import numpy as np
    allowed_globals['np'] = np
except ImportError:
    pass

allowed_globals.update(context_payload)

exec_scope = {{}}
try:
    exec({repr(code_str)}, allowed_globals, exec_scope)
    result_val = exec_scope.get('result', None)
    output = {{
        'status': 'SUCCESS',
        'result': str(result_val) if result_val is not None else 'Executed successfully',
        'scope': {{k: str(v) for k, v in exec_scope.items() if not k.startswith('_')}}
    }}
except Exception as err:
    output = {{
        'status': 'ERROR',
        'error': f"{{type(err).__name__}}: {{err}}"
    }}

print(json.dumps(output))
"""

        try:
            proc = subprocess.run(
                [sys.executable, "-c", runner_script],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if proc.returncode != 0 and not proc.stdout.strip():
                return {
                    "status": "ERROR",
                    "error": proc.stderr.strip() or f"Subprocess exited with returncode {proc.returncode}",
                }
            try:
                res_dict = json.loads(proc.stdout.strip())
                return res_dict
            except Exception:
                return {"status": "SUCCESS", "raw_output": proc.stdout.strip()}
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT_EXCEEDED",
                "error": f"Execution aborted: Subprocess exceeded maximum timeout limit ({timeout}s).",
            }

    @staticmethod
    def execute_sql(sql_query: str) -> Dict[str, Any]:
        """Sanitizes SQL query and returns read-only execution context."""
        sanitized_query = SQLQuerySanitizer.sanitize(sql_query)
        return {
            "status": "SUCCESS",
            "sanitized_query": sanitized_query,
            "isolation_mode": "READ_ONLY",
        }


# ---------------------------------------------------------------------------
# OpenAI Syntax Generator Helper
# ---------------------------------------------------------------------------

def generate_and_execute_syntax(prompt: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generates syntax from OpenAI model and executes inside Secure Sandbox."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return {"status": "ERROR", "error": "OPENAI_API_KEY not configured."}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            store=True,
        )
        generated_code = response.output_text
        return SecureSandboxExecutor.execute_python(generated_code)
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc)}


if __name__ == "__main__":
    demo_code = "result = [x * 2 for x in range(5)]"
    print("Testing Sandbox Execution:")
    print(SecureSandboxExecutor.execute_python(demo_code))