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
# AST Dead Code & Unused Variable Inspector
# ---------------------------------------------------------------------------

class ASTDeadCodeInspector(ast.NodeVisitor):
    """AST Inspector detecting unused local variables and dead code statements after return/raise."""

    def __init__(self):
        self.function_scopes: List[Dict[str, Any]] = []
        self.unused_variables: List[Dict[str, Any]] = []
        self.dead_code: List[Dict[str, Any]] = []

    def _scan_body(self, body: Any) -> None:
        if not isinstance(body, list):
            return
        terminator = None
        for stmt in body:
            if terminator is not None:
                stmt_repr = ast.unparse(stmt) if hasattr(ast, 'unparse') else type(stmt).__name__
                self.dead_code.append({
                    "line": getattr(stmt, "lineno", -1),
                    "statement": stmt_repr,
                    "type": type(stmt).__name__,
                    "after": type(terminator).__name__,
                    "message": f"Dead code statement '{type(stmt).__name__}' at line {getattr(stmt, 'lineno', -1)} appears after '{type(terminator).__name__}'."
                })
            elif isinstance(stmt, (ast.Return, ast.Raise)):
                terminator = stmt

    def visit_Module(self, node: ast.Module):
        self._scan_body(node.body)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._scan_body(node.body)
        scope = {
            "name": node.name,
            "defined": {},
            "loaded": set()
        }
        self.function_scopes.append(scope)
        self.generic_visit(node)
        popped = self.function_scopes.pop()
        for var_name, lineno in popped["defined"].items():
            if var_name not in popped["loaded"] and not var_name.startswith("_"):
                self.unused_variables.append({
                    "name": var_name,
                    "line": lineno,
                    "function": popped["name"],
                    "message": f"Unused variable '{var_name}' defined at line {lineno} in function '{popped['name']}'."
                })

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_If(self, node: ast.If):
        self._scan_body(node.body)
        self._scan_body(node.orelse)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._scan_body(node.body)
        self._scan_body(node.orelse)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._scan_body(node.body)
        self._scan_body(node.orelse)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self._scan_body(node.body)
        self._scan_body(node.orelse)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self._scan_body(node.body)
        self._scan_body(node.orelse)
        self._scan_body(node.finalbody)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self._scan_body(node.body)
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        self._scan_body(node.body)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._scan_body(node.body)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if self.function_scopes:
            current_scope = self.function_scopes[-1]
            if isinstance(node.ctx, ast.Store):
                if node.id not in current_scope["defined"]:
                    current_scope["defined"][node.id] = getattr(node, "lineno", -1)
            elif isinstance(node.ctx, ast.Load):
                for sc in self.function_scopes:
                    sc["loaded"].add(node.id)
        self.generic_visit(node)

    @classmethod
    def inspect(cls, code_str: str) -> Dict[str, Any]:
        """Parses python code AST and detects unused variables and dead code statements."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as syn_err:
            raise SecurityValidationError(f"Invalid Python syntax: {syn_err}") from syn_err

        inspector = cls()
        inspector.visit(tree)
        return {
            "unused_variables": inspector.unused_variables,
            "dead_code": inspector.dead_code,
            "has_dead_code": len(inspector.dead_code) > 0,
            "has_unused_variables": len(inspector.unused_variables) > 0,
        }


# ---------------------------------------------------------------------------
# Offline Code Template Generator & Syntax Snippet Library (CR-631)
# ---------------------------------------------------------------------------

class OfflineCodeTemplateGenerator:
    """Offline code snippet engine matching request keywords to language templates."""

    TEMPLATES = {
        "python": {
            "function": (
                "def calculate_total(items, tax_rate=0.05):\n"
                "    \"\"\"Calculates total amount including tax.\"\"\"\n"
                "    subtotal = sum(item.get('price', 0) for item in items)\n"
                "    return round(subtotal * (1 + tax_rate), 2)"
            ),
            "class": (
                "class DataProcessor:\n"
                "    \"\"\"Processes and filters structured dataset records.\"\"\"\n"
                "    def __init__(self, records=None):\n"
                "        self.records = records or []\n\n"
                "    def get_active(self):\n"
                "        return [r for r in self.records if r.get('active', True)]"
            ),
            "list_comp": (
                "# Python list comprehension pattern\n"
                "numbers = [1, 2, 3, 4, 5, 6]\n"
                "result = [x * 2 for x in numbers if x % 2 == 0]"
            ),
            "default": (
                "def main():\n"
                "    \"\"\"Standard Python boilerplate entrypoint.\"\"\"\n"
                "    print('Executing offline Python template')\n"
                "    return True\n\n"
                "if __name__ == '__main__':\n"
                "    main()"
            ),
        },
        "javascript": {
            "fetch": (
                "async function fetchResource(url) {\n"
                "    try {\n"
                "        const response = await fetch(url);\n"
                "        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);\n"
                "        return await response.json();\n"
                "    } catch (err) {\n"
                "        console.error('Fetch failed:', err);\n"
                "        throw err;\n"
                "    }\n"
                "}"
            ),
            "express": (
                "const express = require('express');\n"
                "const router = express.Router();\n\n"
                "router.get('/api/resource', (req, res) => {\n"
                "    res.json({ status: 'success', data: [] });\n"
                "});\n\n"
                "module.exports = router;"
            ),
            "default": (
                "function processData(items) {\n"
                "    // JavaScript data transformation snippet\n"
                "    return items.filter(x => Boolean(x)).map(x => x.trim());\n"
                "}"
            ),
        },
        "sql": {
            "select": (
                "SELECT id, name, email, created_at\n"
                "FROM users\n"
                "WHERE status = 'ACTIVE'\n"
                "ORDER BY created_at DESC;"
            ),
            "join": (
                "SELECT o.id AS order_id, u.name AS user_name, o.total_amount\n"
                "FROM orders o\n"
                "JOIN users u ON o.user_id = u.id\n"
                "WHERE o.status = 'COMPLETED';"
            ),
            "create": (
                "CREATE TABLE IF NOT EXISTS items (\n"
                "    id SERIAL PRIMARY KEY,\n"
                "    title VARCHAR(255) NOT NULL,\n"
                "    price NUMERIC(10, 2) NOT NULL,\n"
                "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
                ");"
            ),
            "default": (
                "SELECT * FROM records LIMIT 100;"
            ),
        },
        "html": {
            "form": (
                "<form action=\"/submit\" method=\"POST\" class=\"form-container\">\n"
                "    <label for=\"name\">Name:</label>\n"
                "    <input type=\"text\" id=\"name\" name=\"name\" required />\n"
                "    <label for=\"email\">Email:</label>\n"
                "    <input type=\"email\" id=\"email\" name=\"email\" required />\n"
                "    <button type=\"submit\">Submit</button>\n"
                "</form>"
            ),
            "table": (
                "<table class=\"data-table\">\n"
                "    <thead>\n"
                "        <tr><th>ID</th><th>Name</th><th>Status</th></tr>\n"
                "    </thead>\n"
                "    <tbody>\n"
                "        <tr><td>1</td><td>Sample Item</td><td>Active</td></tr>\n"
                "    </tbody>\n"
                "</table>"
            ),
            "default": (
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>Offline HTML Template</title>\n"
                "</head>\n"
                "<body>\n"
                "    <h1>Welcome</h1>\n"
                "</body>\n"
                "</html>"
            ),
        },
    }

    @classmethod
    def detect_language(cls, prompt: str) -> str:
        """Infers language from request prompt keywords."""
        p_lower = prompt.lower()
        if any(k in p_lower for k in ["select", "join", "sql", "query", "database", "insert into", "create table"]):
            return "sql"
        if any(k in p_lower for k in ["html", "<form", "<div", "<table", "markup", "web page", "dom"]):
            return "html"
        if any(k in p_lower for k in ["javascript", "js", "fetch", "node", "express", "react", "async function"]):
            return "javascript"
        return "python"

    @classmethod
    def render_template(cls, prompt: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Matches request keywords and returns rendered boilerplate code."""
        lang = language.lower() if language else cls.detect_language(prompt)
        if lang not in cls.TEMPLATES:
            lang = "python"

        p_lower = prompt.lower()
        templates_for_lang = cls.TEMPLATES[lang]
        matched_pattern = "default"

        if lang == "python":
            if any(k in p_lower for k in ["class", "oop", "object"]):
                matched_pattern = "class"
            elif any(k in p_lower for k in ["list", "comprehension", "filter"]):
                matched_pattern = "list_comp"
            elif any(k in p_lower for k in ["function", "def", "calculate"]):
                matched_pattern = "function"
        elif lang == "javascript":
            if any(k in p_lower for k in ["fetch", "api", "request", "http", "async"]):
                matched_pattern = "fetch"
            elif any(k in p_lower for k in ["express", "router", "route", "server"]):
                matched_pattern = "express"
        elif lang == "sql":
            if any(k in p_lower for k in ["join", "inner join", "left join"]):
                matched_pattern = "join"
            elif any(k in p_lower for k in ["create", "table", "schema"]):
                matched_pattern = "create"
            elif any(k in p_lower for k in ["select", "query", "find"]):
                matched_pattern = "select"
        elif lang == "html":
            if any(k in p_lower for k in ["form", "input", "submit"]):
                matched_pattern = "form"
            elif any(k in p_lower for k in ["table", "grid", "rows"]):
                matched_pattern = "table"

        rendered_code = templates_for_lang.get(matched_pattern, templates_for_lang["default"])

        return {
            "status": "SUCCESS",
            "language": lang,
            "pattern": matched_pattern,
            "code": rendered_code,
            "offline": True,
        }


# ---------------------------------------------------------------------------
# OpenAI Syntax Generator Helper
# ---------------------------------------------------------------------------

def generate_and_execute_syntax(
    prompt: str,
    api_key: Optional[str] = None,
    allow_offline: bool = True,
) -> Dict[str, Any]:
    """
    Generates syntax from OpenAI model and executes inside Secure Sandbox.
    If API key is unconfigured and allow_offline is True, returns an offline code template.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        if allow_offline:
            offline_result = OfflineCodeTemplateGenerator.render_template(prompt)
            return {
                "status": "OFFLINE_TEMPLATE",
                "language": offline_result["language"],
                "pattern": offline_result["pattern"],
                "code": offline_result["code"],
                "offline": True,
                "message": "Returned offline code template because OPENAI_API_KEY is not configured.",
            }
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