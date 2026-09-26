import json

from flask import Flask, render_template, request, jsonify
import pandas as pd

from utils.llm import generate_pandas_code, explain_result
from utils.charts import generate_charts
from utils.data import apply_filters
from utils.safe_exec import execute_safe_code, SecurityViolationError, CodeTimeoutError, sanitize_code
from utils.concurrency import VersionedStore, VersionedEntity, RetryExhaustedError, retry_on_conflict

app = Flask(__name__)

DATASET_KEY = "dataset"
UPDATE_MAX_ATTEMPTS = 25

dataset_store = VersionedStore()


class DatasetMissingError(Exception):
    pass


class RecordNotFoundError(Exception):
    pass


class InvalidUpdateError(ValueError):
    pass


class StaleVersionError(Exception):
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Dataset version is {actual}, but the request expected {expected}.")


def load_dataset(df):
    return dataset_store.put(DATASET_KEY, df)


def reset_dataset():
    dataset_store.delete(DATASET_KEY)


def current_dataset():
    return dataset_store.get(DATASET_KEY)


def missing_dataset_response():
    return jsonify({
        "error": "No dataset uploaded yet. Please upload a dataset first.",
        "status": "error"
    }), 400


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_python_number(value):
    if pd.isna(value):
        return 0
    return value.item() if hasattr(value, "item") else value


def _fits_column(series, value):
    if pd.api.types.is_bool_dtype(series):
        return isinstance(value, bool)
    if pd.api.types.is_integer_dtype(series):
        return isinstance(value, int) and not isinstance(value, bool)
    if pd.api.types.is_float_dtype(series):
        return _is_number(value)
    return True


def _assign(frame, row, column, value):
    if not _fits_column(frame[column], value):
        target = float if pd.api.types.is_integer_dtype(frame[column]) and _is_number(value) else object
        frame[column] = frame[column].astype(target)
    frame.at[row, column] = value


def _serialize_record(df, row):
    return json.loads(df.loc[[row]].to_json(orient="records"))[0]


def _validate_changes(df, changes, increments):
    if not isinstance(changes, dict) or not isinstance(increments, dict):
        raise InvalidUpdateError("'set' and 'increment' must be JSON objects.")
    if not changes and not increments:
        raise InvalidUpdateError("Provide at least one field in 'set' or 'increment'.")
    unknown = [column for column in {**changes, **increments} if column not in df.columns]
    if unknown:
        raise InvalidUpdateError(f"Unknown column(s): {', '.join(map(str, unknown))}")
    overlap = sorted(set(changes) & set(increments))
    if overlap:
        raise InvalidUpdateError(f"Column(s) cannot be both set and incremented: {', '.join(overlap)}")
    for column, amount in increments.items():
        if not _is_number(amount):
            raise InvalidUpdateError(f"Increment for '{column}' must be a number.")
        if not pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(df[column]):
            raise InvalidUpdateError(f"Column '{column}' is not numeric and cannot be incremented.")


@retry_on_conflict(max_attempts=UPDATE_MAX_ATTEMPTS)
def apply_record_update(row, changes=None, increments=None, expected_version=None) -> VersionedEntity:
    changes = changes or {}
    increments = increments or {}

    snapshot = current_dataset()
    if snapshot is None:
        raise DatasetMissingError()
    if expected_version is not None and snapshot.version != expected_version:
        raise StaleVersionError(expected_version, snapshot.version)

    df = snapshot.value
    if row not in df.index:
        raise RecordNotFoundError(row)
    _validate_changes(df, changes, increments)

    updated = df.copy()
    for column, value in changes.items():
        _assign(updated, row, column, value)
    for column, amount in increments.items():
        _assign(updated, row, column, _as_python_number(updated.at[row, column]) + amount)

    return dataset_store.compare_and_set(DATASET_KEY, snapshot.version, updated)


@app.route("/")
def home():
    return render_template("index.html")


# Upload CSV
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    df = pd.read_csv(file)
    entity = load_dataset(df)

    filters = {}
    for col in df.columns:
        if df[col].dtype == "object":
            filters[col] = df[col].dropna().unique().tolist()

    return jsonify({
        "filters": filters,
        "rows": len(df),
        "cols": len(df.columns),
        "version": entity.version
    })


from utils.llm import generate_report

@app.route("/charts")
def charts():
    snapshot = current_dataset()
    if snapshot is None:
        return missing_dataset_response()

    from utils.charts import generate_charts
    from utils.llm import generate_report

    return jsonify({
        "charts": generate_charts(snapshot.value),
        "report": generate_report(snapshot.value),
        "version": snapshot.version
    })

# Filter
@app.route("/filter", methods=["POST"])
def filter_data():
    snapshot = current_dataset()
    if snapshot is None:
        return missing_dataset_response()

    filters = request.json

    df_filtered = snapshot.value.copy()

    # 🔥 Apply filters correctly
    for col, val in filters.items():
        if val:
            df_filtered = df_filtered[df_filtered[col] == val]

    from utils.charts import generate_charts
    from utils.llm import generate_report

    return jsonify({
        "charts": generate_charts(df_filtered),
        "report": generate_report(df_filtered),
        "version": snapshot.version
    })

@app.route("/query", methods=["POST"])
def query():
    snapshot = current_dataset()
    if snapshot is None:
        return missing_dataset_response()

    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "")
    if not question:
        return jsonify({
            "error": "No question provided.",
            "status": "error"
        }), 400

    code = generate_pandas_code(question, snapshot.value.columns)

    try:
        # Secure sandbox execution with AST inspection and timeout bounds
        result = execute_safe_code(code, snapshot.value.copy())
    except SecurityViolationError as e:
        return jsonify({
            "error": f"Security violation detected: {str(e)}",
            "status": "blocked",
            "code": code
        }), 400
    except (CodeTimeoutError, TimeoutError) as e:
        return jsonify({
            "error": f"Execution timeout: {str(e)}",
            "status": "timeout",
            "code": code
        }), 408
    except Exception as e:
        return jsonify({
            "error": f"Execution error: {str(e)}",
            "status": "error",
            "code": code
        }), 400

    explanation = explain_result(question, result)

    return jsonify({
        "result": str(result),
        "explanation": explanation,
        "code": code,
        "status": "success",
        "version": snapshot.version
    })


@app.route("/records/<int:row>", methods=["GET"])
def get_record(row):
    snapshot = current_dataset()
    if snapshot is None:
        return missing_dataset_response()
    if row not in snapshot.value.index:
        return jsonify({"error": f"Record {row} not found.", "status": "error"}), 404

    return jsonify({
        "row": row,
        "record": _serialize_record(snapshot.value, row),
        "version": snapshot.version,
        "status": "success"
    })


@app.route("/records/<int:row>", methods=["PATCH"])
def update_record(row):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object.", "status": "error"}), 400

    expected_version = payload.get("expected_version")
    if expected_version is not None and (not isinstance(expected_version, int) or isinstance(expected_version, bool)):
        return jsonify({"error": "'expected_version' must be an integer.", "status": "error"}), 400

    try:
        entity = apply_record_update(
            row,
            changes=payload.get("set", {}),
            increments=payload.get("increment", {}),
            expected_version=expected_version,
        )
    except DatasetMissingError:
        return missing_dataset_response()
    except RecordNotFoundError:
        return jsonify({"error": f"Record {row} not found.", "status": "error"}), 404
    except InvalidUpdateError as e:
        return jsonify({"error": str(e), "status": "error"}), 400
    except StaleVersionError as e:
        return jsonify({
            "error": str(e),
            "status": "conflict",
            "expected_version": e.expected,
            "current_version": e.actual
        }), 409
    except RetryExhaustedError as e:
        return jsonify({
            "error": f"Update aborted after {e.attempts} conflicting attempts. Please retry.",
            "status": "conflict"
        }), 409

    return jsonify({
        "row": row,
        "record": _serialize_record(entity.value, row),
        "version": entity.version,
        "status": "success"
    })


if __name__ == "__main__":
    app.run(debug=True)
