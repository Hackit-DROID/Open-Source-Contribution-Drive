QUERY_PROMPT = """
You are a pandas expert.

DataFrame name is: df

Columns: {columns}

Convert the question into VALID pandas code.

IMPORTANT:
- Use ONLY df
- Return ONLY expression
- No explanation

Question: {question}
"""

EXPLAIN_PROMPT = """
You are a data analyst.

Explain the result in simple, clear language.

Question: {question}
Result: {result}
"""