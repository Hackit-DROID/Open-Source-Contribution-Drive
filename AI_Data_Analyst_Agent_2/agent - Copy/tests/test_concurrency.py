import os
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pandas as pd

AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

import app as flask_app
from utils.concurrency import (
    DeadlockError,
    RetryExhaustedError,
    SerializationFailureError,
    VersionConflictError,
    VersionedStore,
    is_transient_error,
    retry_on_conflict,
)

CONCURRENT_REQUESTS = 50


class OperationalError(Exception):
    pass


class TestVersionedStore(unittest.TestCase):
    def setUp(self):
        self.store = VersionedStore()

    def test_put_increments_version(self):
        self.assertEqual(self.store.put("k", "a").version, 1)
        self.assertEqual(self.store.put("k", "b").version, 2)
        self.assertEqual(self.store.get("k").value, "b")

    def test_missing_key_has_version_zero(self):
        self.assertIsNone(self.store.get("missing"))
        self.assertEqual(self.store.version("missing"), 0)

    def test_compare_and_set_succeeds_with_matching_version(self):
        self.store.put("k", 1)
        entity = self.store.compare_and_set("k", 1, 2)
        self.assertEqual((entity.value, entity.version), (2, 2))

    def test_compare_and_set_rejects_stale_version(self):
        self.store.put("k", 1)
        self.store.compare_and_set("k", 1, 2)

        with self.assertRaises(VersionConflictError) as ctx:
            self.store.compare_and_set("k", 1, 99)

        self.assertEqual((ctx.exception.expected, ctx.exception.actual), (1, 2))
        self.assertEqual(self.store.get("k").value, 2)
        self.assertEqual(self.store.conflicts, 1)

    def test_compare_and_set_creates_when_expecting_zero(self):
        self.assertEqual(self.store.compare_and_set("new", 0, "x").version, 1)
        with self.assertRaises(VersionConflictError):
            self.store.compare_and_set("other", 3, "x")

    def test_entities_are_immutable(self):
        entity = self.store.put("k", 1)
        with self.assertRaises(Exception):
            entity.version = 10

    def test_update_detects_concurrent_write(self):
        self.store.put("k", 0)

        def mutate(snapshot):
            self.store.put("k", 100)
            return snapshot.value + 1

        with self.assertRaises(VersionConflictError):
            self.store.update("k", mutate)
        self.assertEqual(self.store.get("k").value, 100)

    def test_delete_and_clear(self):
        self.store.put("a", 1)
        self.store.put("b", 1)
        self.store.delete("a")
        self.assertIsNone(self.store.get("a"))
        self.store.clear()
        self.assertIsNone(self.store.get("b"))


class TestRetryDecorator(unittest.TestCase):
    def test_retries_until_success(self):
        calls = []
        delays = []

        @retry_on_conflict(max_attempts=5, jitter=False, sleep=delays.append)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise VersionConflictError("k", 1, 2)
            return "done"

        self.assertEqual(flaky(), "done")
        self.assertEqual(len(calls), 3)
        self.assertEqual(delays, [0.005, 0.01])

    def test_backoff_is_capped(self):
        delays = []

        @retry_on_conflict(max_attempts=6, base_delay=0.01, max_delay=0.03, jitter=False, sleep=delays.append)
        def always_conflicts():
            raise VersionConflictError("k", 1, 2)

        with self.assertRaises(RetryExhaustedError):
            always_conflicts()
        self.assertEqual(delays, [0.01, 0.02, 0.03, 0.03, 0.03])

    def test_raises_retry_exhausted_with_last_error(self):
        @retry_on_conflict(max_attempts=3, sleep=lambda _: None)
        def always_conflicts():
            raise VersionConflictError("k", 1, 2)

        with self.assertRaises(RetryExhaustedError) as ctx:
            always_conflicts()
        self.assertEqual(ctx.exception.attempts, 3)
        self.assertIsInstance(ctx.exception.last_error, VersionConflictError)

    def test_does_not_retry_non_transient_errors(self):
        calls = []

        @retry_on_conflict(max_attempts=5, sleep=lambda _: None)
        def broken():
            calls.append(1)
            raise ValueError("bad input")

        with self.assertRaises(ValueError):
            broken()
        self.assertEqual(len(calls), 1)

    def test_retries_deadlock_and_serialization_failures(self):
        errors = [DeadlockError("deadlock"), SerializationFailureError("serialize"), OperationalError("database is locked")]

        @retry_on_conflict(max_attempts=5, sleep=lambda _: None)
        def flaky():
            if errors:
                raise errors.pop(0)
            return "ok"

        self.assertEqual(flaky(), "ok")
        self.assertEqual(errors, [])

    def test_rejects_invalid_attempts(self):
        with self.assertRaises(ValueError):
            retry_on_conflict(max_attempts=0)

    def test_preserves_function_metadata(self):
        @retry_on_conflict(max_attempts=4)
        def named():
            return 1

        self.assertEqual(named.__name__, "named")
        self.assertEqual(named.max_attempts, 4)


class TestTransientErrorDetection(unittest.TestCase):
    def test_classifies_errors(self):
        pg_error = Exception("conflict")
        pg_error.pgcode = "40001"

        self.assertTrue(is_transient_error(VersionConflictError("k", 1, 2)))
        self.assertTrue(is_transient_error(DeadlockError()))
        self.assertTrue(is_transient_error(pg_error))
        self.assertTrue(is_transient_error(OperationalError("deadlock detected")))
        self.assertFalse(is_transient_error(OperationalError("no such table: records")))
        self.assertFalse(is_transient_error(ValueError("deadlock")))
        self.assertFalse(is_transient_error(KeyError("x")))


class TestStoreStress(unittest.TestCase):
    def test_concurrent_increments_lose_no_updates(self):
        store = VersionedStore()
        store.put("counter", 0)
        start = threading.Barrier(CONCURRENT_REQUESTS)

        @retry_on_conflict(max_attempts=100, base_delay=0.001, max_delay=0.02)
        def increment():
            snapshot = store.get("counter")
            time.sleep(0.001)
            return store.compare_and_set("counter", snapshot.version, snapshot.value + 1)

        def worker():
            start.wait()
            return increment()

        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as pool:
            results = list(pool.map(lambda _: worker(), range(CONCURRENT_REQUESTS)))

        final = store.get("counter")
        self.assertEqual(final.value, CONCURRENT_REQUESTS)
        self.assertEqual(final.version, CONCURRENT_REQUESTS + 1)
        self.assertEqual(sorted(r.version for r in results), list(range(2, CONCURRENT_REQUESTS + 2)))
        self.assertGreater(store.conflicts, 0)


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.app.test_client()
        flask_app.dataset_store.clear()
        flask_app.load_dataset(pd.DataFrame({
            "title": ["Dune", "Emma", "Ulysses"],
            "status": ["available", "available", "checked_out"],
            "copies": [5, 2, 0],
            "checkouts": [0, 0, 0],
            "rating": [4.5, 4.0, 3.5],
        }))
        self.addCleanup(flask_app.dataset_store.clear)


class TestRecordEndpoints(AppTestCase):
    def test_get_record_returns_version(self):
        res = self.client.get("/records/0")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["record"]["title"], "Dune")
        self.assertEqual(data["version"], 1)

    def test_update_sets_and_increments_and_bumps_version(self):
        res = self.client.patch("/records/0", json={
            "set": {"status": "checked_out"},
            "increment": {"copies": -1, "checkouts": 1},
            "expected_version": 1,
        })

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["record"]["status"], "checked_out")
        self.assertEqual(data["record"]["copies"], 4)
        self.assertEqual(data["record"]["checkouts"], 1)

    def test_stale_expected_version_returns_conflict(self):
        self.client.patch("/records/0", json={"increment": {"checkouts": 1}})

        res = self.client.patch("/records/0", json={"set": {"status": "lost"}, "expected_version": 1})

        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertEqual(data["status"], "conflict")
        self.assertEqual((data["expected_version"], data["current_version"]), (1, 2))
        self.assertEqual(flask_app.current_dataset().value.at[0, "status"], "available")

    def test_float_increment_on_integer_column(self):
        res = self.client.patch("/records/1", json={"increment": {"copies": 0.5}})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["record"]["copies"], 2.5)

    def test_updates_do_not_mutate_previous_snapshot(self):
        before = flask_app.current_dataset()
        self.client.patch("/records/0", json={"set": {"status": "checked_out"}})
        self.assertEqual(before.value.at[0, "status"], "available")

    def test_validation_errors(self):
        cases = [
            ({"set": {"missing": 1}}, 400),
            ({"increment": {"title": 1}}, 400),
            ({"increment": {"copies": "1"}}, 400),
            ({"set": {"copies": 1}, "increment": {"copies": 1}}, 400),
            ({}, 400),
            ({"set": []}, 400),
            ({"set": {"status": "x"}, "expected_version": "1"}, 400),
        ]
        for payload, status in cases:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.patch("/records/0", json=payload).status_code, status)
        self.assertEqual(self.client.patch("/records/0", data="nope").status_code, 400)
        self.assertEqual(flask_app.current_dataset().version, 1)

    def test_missing_record_and_dataset(self):
        self.assertEqual(self.client.get("/records/99").status_code, 404)
        self.assertEqual(self.client.patch("/records/99", json={"set": {"status": "x"}}).status_code, 404)
        flask_app.reset_dataset()
        self.assertEqual(self.client.get("/records/0").status_code, 400)
        self.assertEqual(self.client.patch("/records/0", json={"set": {"status": "x"}}).status_code, 400)

    def test_exhausted_retries_return_conflict(self):
        with patch.object(flask_app.dataset_store, "compare_and_set",
                          side_effect=VersionConflictError("dataset", 1, 2)), \
                patch("utils.concurrency.time.sleep"):
            res = self.client.patch("/records/0", json={"increment": {"checkouts": 1}})

        self.assertEqual(res.status_code, 409)
        self.assertIn(f"after {flask_app.UPDATE_MAX_ATTEMPTS}", res.get_json()["error"])

    def test_upload_returns_new_version(self):
        from io import BytesIO

        res = self.client.post("/upload", data={"file": (BytesIO(b"a,b\n1,x\n2,y\n"), "data.csv")},
                               content_type="multipart/form-data")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["version"], 2)
        self.assertEqual(list(flask_app.current_dataset().value.columns), ["a", "b"])

    @patch("app.explain_result", return_value="ok")
    @patch("app.generate_pandas_code", return_value="df['checkouts'].sum()")
    def test_query_reports_snapshot_version(self, mock_gen, mock_explain):
        res = self.client.post("/query", json={"question": "total checkouts"})
        self.assertEqual(res.get_json()["version"], 1)


class TestConcurrentRequestStress(AppTestCase):
    def _run_concurrently(self, send):
        start = threading.Barrier(CONCURRENT_REQUESTS)
        original = flask_app.dataset_store.compare_and_set

        def slow_compare_and_set(*args, **kwargs):
            time.sleep(0.001)
            return original(*args, **kwargs)

        def worker(index):
            client = flask_app.app.test_client()
            start.wait()
            return send(client, index)

        with patch.object(flask_app.dataset_store, "compare_and_set", side_effect=slow_compare_and_set):
            with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as pool:
                return list(pool.map(worker, range(CONCURRENT_REQUESTS)))

    def test_50_concurrent_checkouts_have_zero_state_corruption(self):
        flask_app.load_dataset(pd.DataFrame({
            "title": ["Dune"],
            "copies": [CONCURRENT_REQUESTS],
            "checkouts": [0],
        }))
        initial_version = flask_app.current_dataset().version

        responses = self._run_concurrently(
            lambda client, _: client.patch("/records/0", json={"increment": {"copies": -1, "checkouts": 1}})
        )

        self.assertEqual([r.status_code for r in responses], [200] * CONCURRENT_REQUESTS)
        final = flask_app.current_dataset()
        self.assertEqual(final.value.at[0, "copies"], 0)
        self.assertEqual(final.value.at[0, "checkouts"], CONCURRENT_REQUESTS)
        self.assertEqual(final.value.at[0, "copies"] + final.value.at[0, "checkouts"], CONCURRENT_REQUESTS)
        self.assertEqual(final.version, initial_version + CONCURRENT_REQUESTS)
        versions = sorted(r.get_json()["version"] for r in responses)
        self.assertEqual(versions, list(range(initial_version + 1, initial_version + CONCURRENT_REQUESTS + 1)))
        self.assertGreater(flask_app.dataset_store.conflicts, 0)

    def test_50_concurrent_updates_to_different_rows_are_all_kept(self):
        flask_app.load_dataset(pd.DataFrame({
            "student": [f"s{i}" for i in range(CONCURRENT_REQUESTS)],
            "enrolled": [False] * CONCURRENT_REQUESTS,
        }))

        responses = self._run_concurrently(
            lambda client, index: client.patch(f"/records/{index}", json={"set": {"enrolled": True}})
        )

        self.assertEqual([r.status_code for r in responses], [200] * CONCURRENT_REQUESTS)
        self.assertTrue(flask_app.current_dataset().value["enrolled"].all())

    def test_50_concurrent_requests_with_same_expected_version_allow_single_winner(self):
        version = flask_app.current_dataset().version

        responses = self._run_concurrently(
            lambda client, index: client.patch("/records/0", json={
                "set": {"status": f"reserved-{index}"},
                "expected_version": version,
            })
        )

        codes = [r.status_code for r in responses]
        self.assertEqual(codes.count(200), 1)
        self.assertEqual(codes.count(409), CONCURRENT_REQUESTS - 1)
        winner = next(r.get_json() for r in responses if r.status_code == 200)
        final = flask_app.current_dataset()
        self.assertEqual(final.version, version + 1)
        self.assertEqual(final.value.at[0, "status"], winner["record"]["status"])


if __name__ == "__main__":
    unittest.main()
