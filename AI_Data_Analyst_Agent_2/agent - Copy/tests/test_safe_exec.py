"""Comprehensive security test suite verifying code execution sandbox,
AST inspection, and query sanitization in AI_Data_Analyst_Agent_2.
"""

import os
import sys
import unittest
import pandas as pd
from unittest.mock import patch

# Ensure agent directory is in Python path for test execution
AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

from utils.safe_exec import (
    sanitize_code,
    validate_code,
    execute_safe_code,
    SecurityViolationError,
    CodeTimeoutError,
    ASTSecurityInspector,
)


class TestQuerySanitization(unittest.TestCase):
    """Test sanitization and cleaning of raw LLM outputs."""

    def test_strip_markdown_code_blocks(self):
        code_with_fence = "```python\ndf['salary'].mean()\n```"
        self.assertEqual(sanitize_code(code_with_fence), "df['salary'].mean()")

    def test_strip_plain_markdown_fence(self):
        code = "```\ndf.head(10)\n```"
        self.assertEqual(sanitize_code(code), "df.head(10)")

    def test_strip_trailing_semicolons(self):
        code = "df['age'].max();"
        self.assertEqual(sanitize_code(code), "df['age'].max()")

    def test_strip_leading_python_keyword(self):
        code = "python\ndf['salary'].sum()"
        self.assertEqual(sanitize_code(code), "df['salary'].sum()")

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            sanitize_code(123)  # type: ignore


class TestASTSecurityInspector(unittest.TestCase):
    """Test AST inspection and policy enforcement against malicious payloads."""

    def test_valid_pandas_expressions_pass(self):
        valid_codes = [
            "df['salary'].mean()",
            "df[df['age'] > 30]",
            "df.groupby('dept')['salary'].sum()",
            "df.describe()",
            "df.head(5)",
            "df.sort_values(by='salary', ascending=False)",
            "result = df['score'].max()",
            "len(df)",
            "round(df['price'].mean(), 2)",
        ]
        for code in valid_codes:
            tree = validate_code(code)
            self.assertIsNotNone(tree)

    def test_blocks_direct_imports(self):
        malicious = [
            "import os",
            "import sys",
            "import subprocess",
            "import shutil",
            "from os import system",
            "from subprocess import Popen",
            "import os as my_os",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)

    def test_blocks_dangerous_builtins(self):
        malicious = [
            "eval('1 + 1')",
            "exec('print(1)')",
            "open('/etc/passwd', 'r')",
            "compile('1+1', '', 'eval')",
            "__import__('os').system('ls')",
            "globals()",
            "locals()",
            "vars()",
            "breakpoint()",
            "getattr(df, '__class__')",
            "setattr(df, 'bad', 1)",
            "delattr(df, 'bad')",
            "isinstance(df, object)",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)

    def test_blocks_banned_modules_identifiers(self):
        malicious = [
            "os.system('rm -rf /')",
            "sys.exit(0)",
            "subprocess.run(['ls'])",
            "shutil.rmtree('/tmp')",
            "socket.socket()",
            "requests.get('http://attacker.com')",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)

    def test_blocks_dunder_attributes(self):
        malicious = [
            "df.__class__",
            "df.__class__.__bases__",
            "df.__class__.__mro__[1].__subclasses__()",
            "df.__dict__",
            "df.__doc__",
            "df.__init__",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)

    def test_blocks_file_write_attributes(self):
        malicious = [
            "df.to_csv('output.csv')",
            "df.to_excel('output.xlsx')",
            "df.to_sql('table', 'engine')",
            "df.to_parquet('output.parquet')",
            "df.to_pickle('output.pkl')",
            "df.to_feather('output.feather')",
            "df.to_json('output.json')",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)

    def test_blocks_forbidden_statement_types(self):
        malicious = [
            "def exploit(): return 1",
            "class Exploit: pass",
            "global df",
            "del df['salary']",
            "try:\n    pass\nexcept:\n    pass",
            "raise ValueError('bad')",
        ]
        for code in malicious:
            with self.subTest(code=code):
                with self.assertRaises(SecurityViolationError):
                    validate_code(code)


class TestSafeCodeExecution(unittest.TestCase):
    """Test sandboxed execution with dataframes and timeout enforcement."""

    def setUp(self):
        self.df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie", "David"],
            "dept": ["IT", "HR", "IT", "Finance"],
            "salary": [70000, 50000, 80000, 60000],
            "age": [28, 35, 42, 31],
        })

    def test_successful_expression_evaluation(self):
        result = execute_safe_code("df['salary'].mean()", self.df)
        self.assertEqual(result, 65000.0)

    def test_successful_filter_and_count(self):
        result = execute_safe_code("len(df[df['age'] > 30])", self.df)
        self.assertEqual(result, 3)

    def test_successful_assignment_extraction(self):
        result = execute_safe_code("result = df['salary'].max()", self.df)
        self.assertEqual(result, 80000)

    def test_blocks_malicious_execution(self):
        with self.assertRaises(SecurityViolationError):
            execute_safe_code("__import__('os').system('echo hacked')", self.df)

    def test_blocks_file_read_attempt(self):
        with self.assertRaises(SecurityViolationError):
            execute_safe_code("open('/etc/passwd').read()", self.df)

    def test_empty_code_raises_error(self):
        with self.assertRaises(ValueError):
            execute_safe_code("", self.df)

    def test_execution_timeout(self):
        # A code snippet designed to simulate an infinite or long calculation
        slow_code = "[x for x in range(100000000) if x % 2 == 0]"
        with self.assertRaises(CodeTimeoutError):
            execute_safe_code(slow_code, self.df, timeout=0.1)


class TestAppQueryEndpoint(unittest.TestCase):
    """Test Flask endpoint integration with security sandbox."""

    def setUp(self):
        import app as flask_app
        self.app = flask_app.app
        self.client = self.app.test_client()
        # Set up a sample global dataframe
        flask_app.df_global = pd.DataFrame({
            "dept": ["Engineering", "Marketing", "Engineering"],
            "salary": [90000, 60000, 95000]
        })

    def test_query_no_dataset(self):
        import app as flask_app
        flask_app.df_global = None
        res = self.client.post("/query", json={"question": "What is the average salary?"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("No dataset uploaded", data["error"])

    def test_query_no_question(self):
        res = self.client.post("/query", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("No question provided", data["error"])

    @patch("app.explain_result", return_value="The average salary is 81666.67")
    @patch("app.generate_pandas_code", return_value="df['salary'].mean()")
    def test_query_successful_execution(self, mock_gen, mock_explain):
        res = self.client.post("/query", json={"question": "average salary"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("81666", data["result"])

    @patch("app.generate_pandas_code", return_value="__import__('os').system('ls')")
    def test_query_blocked_malicious_code(self, mock_gen):
        res = self.client.post("/query", json={"question": "hack system"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["status"], "blocked")
        self.assertIn("Security violation detected", data["error"])


if __name__ == "__main__":
    unittest.main()
