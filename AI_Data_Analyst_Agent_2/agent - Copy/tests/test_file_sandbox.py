import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import pandas as pd

AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

import app as flask_app
from utils.file_sandbox import (
    FileSandbox,
    SandboxQuotaError,
    SandboxViolationError,
    cleanup_stale_sandboxes,
    current_sandbox,
)
from utils.safe_exec import SecurityViolationError, execute_safe_code, validate_code


class SandboxTestCase(unittest.TestCase):
    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="sandbox-tests-"))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.root = os.path.join(self.base, "scratch")
        self.outside = os.path.join(self.base, "outside")
        os.makedirs(self.outside)
        self.sandbox = FileSandbox(root=self.root, max_bytes=10_000, max_files=5)
        self.addCleanup(self.sandbox.cleanup)
        self.df = pd.DataFrame({"dept": ["IT", "HR", "IT"], "salary": [70000, 50000, 80000]})

    def run_code(self, code, **kwargs):
        return execute_safe_code(code, self.df, sandbox=self.sandbox, **kwargs)

    def assertNothingOutside(self):
        self.assertEqual(os.listdir(self.outside), [])


class TestSandboxPathResolution(SandboxTestCase):
    def test_sandbox_directory_is_created_under_scratch_root(self):
        self.assertTrue(os.path.isdir(self.sandbox.directory))
        self.assertEqual(os.path.dirname(self.sandbox.directory), os.path.realpath(self.root))

    def test_relative_paths_resolve_inside_sandbox(self):
        resolved = self.sandbox.resolve("reports/summary.csv")
        self.assertEqual(resolved, os.path.join(self.sandbox.directory, "reports", "summary.csv"))

    def test_rejects_paths_escaping_the_sandbox(self):
        for path in ("../escape.txt", "a/../../escape.txt", os.path.join(self.outside, "x.txt"), "/etc/passwd", "", "."):
            with self.subTest(path=path), self.assertRaises(SandboxViolationError):
                self.sandbox.resolve(path)

    def test_rejects_symlink_pointing_outside(self):
        os.symlink(self.outside, os.path.join(self.sandbox.directory, "link"))

        with self.assertRaises(SandboxViolationError):
            self.sandbox.resolve("link/evil.txt")

    def test_violation_is_a_security_violation(self):
        self.assertTrue(issubclass(SandboxViolationError, SecurityViolationError))


class TestSandboxedExecution(SandboxTestCase):
    def test_allows_writes_inside_sandbox(self):
        self.run_code("df.to_csv(scratch_path('out.csv'), index=False)")
        self.run_code("f = open('notes.txt', 'w')\nf.write('hello')\nf.close()")

        self.assertEqual(
            [item["name"] for item in self.sandbox.list_files()],
            ["notes.txt", "out.csv"],
        )
        with open(os.path.join(self.sandbox.directory, "out.csv")) as handle:
            self.assertEqual(handle.readline().strip(), "dept,salary")

    def test_allows_nested_directories_inside_sandbox(self):
        self.run_code("df.to_json(scratch_path('reports/2026/data.json'))")
        self.assertEqual(self.sandbox.list_files()[0]["name"], os.path.join("reports", "2026", "data.json"))

    def test_code_can_read_back_its_own_files(self):
        result = self.run_code(
            "df.to_csv(scratch_path('out.csv'), index=False)\nresult = open('out.csv').read().splitlines()[0]"
        )
        self.assertEqual(result, "dept,salary")

    def test_blocks_writes_outside_sandbox(self):
        target = os.path.join(self.outside, "leak.csv")
        attempts = [
            f"df.to_csv({target!r})",
            f"df.to_json({target!r})",
            f"df.to_html({target!r})",
            f"df.to_string(buf={target!r})",
            f"np.savetxt({target!r}, df[['salary']].values)",
            f"np.save({target!r}, df['salary'].values)",
            f"open({target!r}, 'w')",
            f"open({target!r}, 'a')",
            "open('../escape.txt', 'w')",
            f"df.to_csv(SCRATCH_DIR + '/../escape.csv')",
        ]
        for code in attempts:
            with self.subTest(code=code), self.assertRaises(SecurityViolationError):
                self.run_code(code)
        self.assertNothingOutside()
        self.assertFalse(os.path.exists(os.path.join(self.root, "escape.csv")))

    def test_blocks_relative_pandas_writes_into_working_directory(self):
        cwd = os.getcwd()
        os.chdir(self.outside)
        self.addCleanup(os.chdir, cwd)

        with self.assertRaises(SandboxViolationError):
            self.run_code("df.to_csv('relative.csv')")
        self.assertNothingOutside()

    def test_blocks_reading_outside_sandbox_via_sandboxed_open(self):
        with self.assertRaises(SandboxViolationError):
            self.run_code("open('/etc/passwd').read()")

    def test_blocks_symlink_escape_during_execution(self):
        os.symlink(self.outside, os.path.join(self.sandbox.directory, "link"))

        with self.assertRaises(SecurityViolationError):
            self.run_code("df.to_csv(SCRATCH_DIR + '/link/evil.csv')")
        self.assertNothingOutside()

    def test_enforces_storage_quota(self):
        with self.assertRaises(SandboxQuotaError):
            self.run_code("f = open('big.txt', 'w')\nf.write('x' * 20000)\nf.close()")

    def test_enforces_file_count_quota(self):
        with self.assertRaises(SandboxQuotaError):
            self.run_code("\n".join(f"open('f{i}.txt', 'w').close()" for i in range(6)))
        self.assertLessEqual(len(self.sandbox.list_files()), 5)

    def test_sandbox_is_deactivated_after_execution(self):
        self.run_code("df.to_csv(scratch_path('out.csv'))")
        self.assertIsNone(current_sandbox())

        path = os.path.join(self.outside, "allowed.txt")
        with open(path, "w") as handle:
            handle.write("host code is not restricted")
        self.assertTrue(os.path.exists(path))

    def test_restriction_does_not_leak_to_other_threads(self):
        started = threading.Event()
        written = []

        def host_writer():
            started.wait(2)
            path = os.path.join(self.outside, "other-thread.txt")
            with open(path, "w") as handle:
                handle.write("ok")
            written.append(path)

        thread = threading.Thread(target=host_writer)
        thread.start()
        self.sandbox.activate()
        try:
            started.set()
            thread.join(2)
        finally:
            self.sandbox.deactivate()

        self.assertEqual(len(written), 1)

    def test_writes_still_blocked_by_ast_without_sandbox(self):
        for code in ("df.to_csv('out.csv')", "open('out.txt', 'w')"):
            with self.subTest(code=code), self.assertRaises(SecurityViolationError):
                execute_safe_code(code, self.df)
        with self.assertRaises(SecurityViolationError):
            validate_code("df.to_parquet('x.parquet')", allow_file_writes=True)
        with self.assertRaises(SecurityViolationError):
            validate_code("df.read_csv('x.csv')", allow_file_writes=True)

    def test_blocks_file_mutation_outside_sandbox(self):
        victim = os.path.join(self.outside, "victim.txt")
        with open(victim, "w") as handle:
            handle.write("keep me")

        with self.assertRaises(SandboxViolationError):
            self.sandbox.activate()
            try:
                os.remove(victim)
            finally:
                self.sandbox.deactivate()
        self.assertTrue(os.path.exists(victim))


class TestSandboxCleanup(SandboxTestCase):
    def test_cleanup_removes_generated_files(self):
        self.run_code("df.to_csv(scratch_path('out.csv'))")
        directory = self.sandbox.directory

        self.sandbox.cleanup()

        self.assertFalse(os.path.exists(directory))
        self.assertTrue(self.sandbox.closed)
        self.assertEqual(self.sandbox.list_files(), [])

    def test_cleanup_is_idempotent_and_blocks_reuse(self):
        self.sandbox.cleanup()
        self.sandbox.cleanup()
        with self.assertRaises(SandboxViolationError):
            self.sandbox.activate()

    def test_context_manager_cleans_up(self):
        with FileSandbox(root=self.root) as sandbox:
            execute_safe_code("df.to_csv(scratch_path('out.csv'))", self.df, sandbox=sandbox)
            directory = sandbox.directory
            self.assertTrue(os.path.exists(os.path.join(directory, "out.csv")))
        self.assertFalse(os.path.exists(directory))

    def test_cleanup_stale_sandboxes(self):
        stale = FileSandbox(root=self.root)
        fresh = FileSandbox(root=self.root)
        self.addCleanup(fresh.cleanup)
        old = time.time() - 7200
        os.utime(stale.directory, (old, old))
        keep = os.path.join(self.root, "not-a-sandbox")
        os.makedirs(keep)
        os.utime(keep, (old, old))

        removed = cleanup_stale_sandboxes(self.root, max_age=3600)

        self.assertEqual(removed, 1)
        self.assertFalse(os.path.exists(stale.directory))
        self.assertTrue(os.path.exists(fresh.directory))
        self.assertTrue(os.path.exists(keep))


class TestQueryEndpointSandbox(unittest.TestCase):
    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="sandbox-app-"))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.root = os.path.join(self.base, "scratch")
        self.outside = os.path.join(self.base, "outside")
        os.makedirs(self.outside)
        config = patch.dict(flask_app.app.config, {
            "SANDBOX_SCRATCH_DIR": self.root,
            "SANDBOX_MAX_BYTES": 10_000,
            "SANDBOX_MAX_FILES": 5,
        })
        config.start()
        self.addCleanup(config.stop)
        flask_app.load_dataset(pd.DataFrame({"dept": ["IT", "HR"], "salary": [70000, 50000]}))
        self.addCleanup(flask_app.dataset_store.clear)
        self.client = flask_app.app.test_client()

    def sandboxes(self):
        if not os.path.isdir(self.root):
            return []
        return [name for name in os.listdir(self.root) if name.startswith("sandbox-")]

    def post(self, code):
        with patch("app.generate_pandas_code", return_value=code), \
                patch("app.explain_result", return_value="ok"):
            return self.client.post("/query", json={"question": "q"})

    def test_generated_files_are_reported_and_removed_after_response(self):
        res = self.post("df.to_csv(scratch_path('report.csv'), index=False)\nresult = len(df)")

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual([item["name"] for item in data["files"]], ["report.csv"])
        self.assertGreater(data["files"][0]["size"], 0)
        res.close()
        self.assertEqual(self.sandboxes(), [])

    def test_write_outside_sandbox_is_blocked_and_cleaned_up(self):
        target = os.path.join(self.outside, "leak.csv")

        res = self.post(f"df.to_csv({target!r})")

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["status"], "blocked")
        self.assertIn("only allowed inside the sandbox directory", res.get_json()["error"])
        res.close()
        self.assertFalse(os.path.exists(target))
        self.assertEqual(self.sandboxes(), [])

    def test_quota_violation_returns_413(self):
        res = self.post("f = open('big.txt', 'w')\nf.write('x' * 20000)\nf.close()")

        self.assertEqual(res.status_code, 413)
        self.assertIn("quota", res.get_json()["error"])
        res.close()
        self.assertEqual(self.sandboxes(), [])

    def test_each_request_gets_isolated_sandbox(self):
        first = self.post("f = open('a.txt', 'w')\nf.write('1')\nf.close()\nresult = 1")
        second = self.post("result = 2")

        self.assertEqual([item["name"] for item in first.get_json()["files"]], ["a.txt"])
        self.assertEqual(second.get_json()["files"], [])
        first.close()
        second.close()
        self.assertEqual(self.sandboxes(), [])

    def test_sandbox_removed_when_explanation_fails(self):
        with patch("app.generate_pandas_code", return_value="df.to_csv(scratch_path('x.csv'))"), \
                patch("app.explain_result", side_effect=RuntimeError("llm down")):
            res = self.client.post("/query", json={"question": "q"})
        self.assertEqual(res.status_code, 500)
        self.assertEqual(self.sandboxes(), [])


if __name__ == "__main__":
    unittest.main()
