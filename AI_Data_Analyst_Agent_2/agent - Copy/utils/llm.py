import os
from groq import Groq
from dotenv import load_dotenv
from prompts.prompts import QUERY_PROMPT, EXPLAIN_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_report(df):
    prompt = f"""
    Analyze this dataset and give insights:
    Columns: {list(df.columns)}
    Sample: {df.head(5).to_string()}
    """

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

def generate_pandas_code(question, columns):
    prompt = QUERY_PROMPT.format(question=question, columns=columns)

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()


def explain_result(question, result):
    prompt = EXPLAIN_PROMPT.format(question=question, result=result)

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()