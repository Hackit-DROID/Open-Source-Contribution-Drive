import unittest
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src import (
    ASTSecurityInspector,
    ASTDeadCodeInspector,
    SQLQuerySanitizer,
    SecureSandboxExecutor,
    SecurityValidationError,
)


class SecuritySandboxPenetrationTest(unittest.TestCase):
    """Penetration test suite verifying AST inspection, query sanitization, and subprocess isolation."""

    # -------------------------------------------------------------------
    # 1. AST Inspector Penetration Tests
    # -------------------------------------------------------------------

    def test_ast_blocks_forbidden_imports(self):
        """Verify AST inspector blocks forbidden imports (os, sys, subprocess, socket, shutil)."""
        malicious_payloads = [
            "import os\nos.system('whoami')",
            "import sys\nsys.exit(0)",
            "import subprocess\nsubprocess.Popen(['ls', '-la'])",
            "import socket\ns = socket.socket()",
            "import shutil\nshutil.rmtree('/')",
            "from os import system\nsystem('dir')",
            "from subprocess import Popen",
        ]
        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(SecurityValidationError):
                    ASTSecurityInspector.inspect(payload)

    def test_ast_blocks_forbidden_builtins(self):
        """Verify AST inspector blocks forbidden builtins (eval, exec, open, __import__)."""
        malicious_payloads = [
            "eval(\"__import__('os').system('echo pwned')\")",
            "exec(\"import sys\")",
            "f = open('/etc/passwd', 'r')",
            "mod = __import__('os')",
            "globals()['os']",
            "locals()['sys']",
            "getattr(object, '__subclasses__')",
        ]
        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(SecurityValidationError):
                    ASTSecurityInspector.inspect(payload)

    def test_ast_blocks_subclass_traversal(self):
        """Verify AST inspector blocks subclass traversal and object introspection payloads."""
        malicious_payloads = [
            "x = ().__class__.__base__.__subclasses__()",
            "y = ''.__class__.__mro__[1].__subclasses__()",
            "z = object.__subclasses__()",
        ]
        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(SecurityValidationError):
                    ASTSecurityInspector.inspect(payload)

    # -------------------------------------------------------------------
    # 2. SQL Query Sanitizer Penetration Tests
    # -------------------------------------------------------------------

    def test_sql_sanitizer_blocks_destructive_queries(self):
        """Verify SQL sanitizer blocks DDL, DML, and comment injection attempts."""
        destructive_queries = [
            "DROP TABLE users;",
            "DELETE FROM accounts WHERE 1=1;",
            "UPDATE users SET is_admin = 1;",
            "ALTER TABLE data ADD COLUMN secret text;",
            "INSERT INTO logs VALUES ('hack');",
            "TRUNCATE TABLE audit_trail;",
            "SELECT * FROM users; -- comment injection",
            "SELECT * FROM users /* inline comment */ WHERE 1=1",
            "GRANT ALL PRIVILEGES ON *.* TO 'attacker'@'%'",
        ]
        for query in destructive_queries:
            with self.subTest(query=query):
                with self.assertRaises(SecurityValidationError):
                    SQLQuerySanitizer.sanitize(query)

    def test_sql_sanitizer_allows_select(self):
        """Verify SQL sanitizer permits read-only SELECT and WITH queries."""
        legitimate_queries = [
            "SELECT id, name FROM users WHERE active = 1",
            "WITH total_sales AS (SELECT SUM(amount) AS total FROM sales) SELECT * FROM total_sales",
            "SELECT COUNT(*) FROM orders",
        ]
        for query in legitimate_queries:
            with self.subTest(query=query):
                clean = SQLQuerySanitizer.sanitize(query)
                self.assertTrue(clean.startswith("SELECT ") or clean.startswith("WITH "))

    # -------------------------------------------------------------------
    # 3. Subprocess Execution Isolation & Timeout Tests
    # -------------------------------------------------------------------

    def test_subprocess_timeout_isolation(self):
        """Verify infinite loops or hanging execution are killed by timeout limit."""
        infinite_loop_payload = "while True: pass"
        start_time = time.time()
        res = SecureSandboxExecutor.execute_python(infinite_loop_payload, timeout=0.5)
        elapsed = time.time() - start_time

        self.assertEqual(res.get("status"), "TIMEOUT_EXCEEDED")
        self.assertLess(elapsed, 2.0)

    def test_legitimate_code_execution(self):
        """Verify safe Python data structures and operations execute cleanly."""
        safe_code = """
items = [1, 2, 3, 4, 5]
squared = [x ** 2 for x in items]
result = sum(squared)
"""
        res = SecureSandboxExecutor.execute_python(safe_code)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("result"), "55")


# -----------------------------------------------------------------------
# 4. AST Dead Code and Unused Variable Inspector Tests (CR-860)
# -----------------------------------------------------------------------

class ASTDeadCodeInspectorTest(unittest.TestCase):
    """Test suite verifying detection of unused variables and dead code statements."""

    def test_detects_unused_variables_in_functions(self):
        """Verify inspector identifies variables defined in a function that are never referenced."""
        code = """
def process_data(val):
    temp_unused = val * 10
    active_calc = val + 5
    result = active_calc * 2
    return result
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertTrue(res["has_unused_variables"])
        unused_names = [v["name"] for v in res["unused_variables"]]
        self.assertIn("temp_unused", unused_names)
        self.assertNotIn("active_calc", unused_names)
        self.assertNotIn("result", unused_names)

    def test_no_false_positive_when_variables_used(self):
        """Verify clean code with all variables referenced produces zero unused variable flags."""
        code = """
def calculate(a, b):
    total = a + b
    factor = 2
    return total * factor
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertFalse(res["has_unused_variables"])
        self.assertEqual(len(res["unused_variables"]), 0)

    def test_detects_dead_code_after_return(self):
        """Verify statements appearing after a return statement are flagged as dead code."""
        code = """
def fetch_status():
    status = "OK"
    return status
    print("This is unreachable log")
    status = "ERROR"
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertTrue(res["has_dead_code"])
        self.assertEqual(len(res["dead_code"]), 2)
        statements = [d["type"] for d in res["dead_code"]]
        self.assertIn("Expr", statements)
        self.assertIn("Assign", statements)
        self.assertEqual(res["dead_code"][0]["after"], "Return")

    def test_detects_dead_code_after_raise(self):
        """Verify statements appearing after a raise statement are flagged as dead code."""
        code = """
def validate_age(age):
    if age < 0:
        raise ValueError("Negative age")
        age = 0
    return age
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertTrue(res["has_dead_code"])
        self.assertEqual(len(res["dead_code"]), 1)
        self.assertEqual(res["dead_code"][0]["type"], "Assign")
        self.assertEqual(res["dead_code"][0]["after"], "Raise")

    def test_no_dead_code_in_valid_branching(self):
        """Verify legitimate if/else branching with returns in separate paths has no dead code."""
        code = """
def compute_sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertFalse(res["has_dead_code"])
        self.assertEqual(len(res["dead_code"]), 0)

    def test_detects_both_unused_variables_and_dead_code(self):
        """Verify code containing both dead code and unused variables flags both."""
        code = """
def complex_fn(x):
    unused_debug_metric = 999
    res = x + 1
    return res
    extra_metric = 123
"""
        res = ASTDeadCodeInspector.inspect(code)
        self.assertTrue(res["has_unused_variables"])
        self.assertTrue(res["has_dead_code"])
        unused_names = [v["name"] for v in res["unused_variables"]]
        self.assertIn("unused_debug_metric", unused_names)
        self.assertIn("extra_metric", unused_names)
        self.assertEqual(len(res["dead_code"]), 1)


if __name__ == "__main__":
    unittest.main()
