from flask import Flask, render_template, request, jsonify
import pandas as pd

from utils.llm import generate_pandas_code, explain_result
from utils.charts import generate_charts
from utils.data import apply_filters

app = Flask(__name__)

df_global = None


@app.route("/")
def home():
    return render_template("index.html")


# Upload CSV
@app.route("/upload", methods=["POST"])
def upload():
    global df_global

    file = request.files["file"]
    df_global = pd.read_csv(file)

    filters = {}
    for col in df_global.columns:
        if df_global[col].dtype == "object":
            filters[col] = df_global[col].dropna().unique().tolist()

    return jsonify({
        "filters": filters,
        "rows": len(df_global),
        "cols": len(df_global.columns)
    })


from utils.llm import generate_report

@app.route("/charts")
def charts():
    global df_global

    from utils.charts import generate_charts
    from utils.llm import generate_report

    return jsonify({
        "charts": generate_charts(df_global),
        "report": generate_report(df_global)
    })

# Filter
@app.route("/filter", methods=["POST"])
def filter_data():
    global df_global

    filters = request.json

    df_filtered = df_global.copy()

    # 🔥 Apply filters correctly
    for col, val in filters.items():
        if val:
            df_filtered = df_filtered[df_filtered[col] == val]

    from utils.charts import generate_charts
    from utils.llm import generate_report

    return jsonify({
        "charts": generate_charts(df_filtered),
        "report": generate_report(df_filtered)
    })

@app.route("/query", methods=["POST"])
def query():
    global df_global

    question = request.json["question"]

    code = generate_pandas_code(question, df_global.columns)

    try:
        # 🔥 SAFE EXECUTION
        local_vars = {"df": df_global}
        exec(f"result = {code}", {}, local_vars)
        result = local_vars["result"]

    except Exception as e:
        return jsonify({
            "error": f"Execution error: {str(e)}",
            "code": code
        })

    explanation = explain_result(question, result)

    return jsonify({
        "result": str(result),
        "explanation": explanation,
        "code": code   # debug
    })

if __name__ == "__main__":
    app.run(debug=True)