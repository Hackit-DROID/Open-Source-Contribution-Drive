import os
from dotenv import load_dotenv

load_dotenv()

print("Python setup successful")
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model="gpt-5-nano",
    input="Hello OpenAI can u give me names of string methods in java "
)

print(response.output_text)

