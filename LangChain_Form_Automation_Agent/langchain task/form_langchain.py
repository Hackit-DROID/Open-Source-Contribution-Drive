import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
import pandas as pd

llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="openai/gpt-3.5-turbo"
)

DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/12uWwn4JHwYrqiSH4_yVr-LqnuNW8jrC-eV9Rp2x534Q/gviz/tq?tqx=out:csv"
SHEET_URL = os.getenv("GOOGLE_SHEET_CSV_URL", DEFAULT_SHEET_URL)

def run_form_langchain():
    # Read Google Sheet
    df = pd.read_csv(SHEET_URL)
    print("Columns:", df.columns)

    # Last response question (2nd column)
    question = df.iloc[-1][df.columns[1]]
    response = llm.invoke(question)

    print("User Question:", question)
    print("LangChain Answer:", response.content)
    return response.content

if __name__ == "__main__":
    run_form_langchain()
