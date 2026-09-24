import unittest
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src import (
    ASTSecurityInspector,
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


if __name__ == "__main__":
    unittest.main()
