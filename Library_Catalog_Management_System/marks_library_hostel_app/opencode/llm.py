from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class OpenCodeLLM:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("API key not found. Check .env file")

        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content