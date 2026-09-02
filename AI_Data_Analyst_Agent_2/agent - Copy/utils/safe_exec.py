def execute_safe_code(code, df):
    allowed_names = {"df": df}

    # ❌ block dangerous keywords
    banned = ["import", "open", "os", "sys", "__"]

    for word in banned:
        if word in code:
            return "Unsafe code detected"

    try:
        return eval(code, {"__builtins__": {}}, allowed_names)
    except Exception as e:
        return str(e)