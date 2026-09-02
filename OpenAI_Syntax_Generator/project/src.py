import os
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

response = client.responses.create(
  model="gpt-5-nano",
  input="write python list data sturucture syntax, example.",
  store=True,
)
print(response.output_text);

#input="write python list data structure"