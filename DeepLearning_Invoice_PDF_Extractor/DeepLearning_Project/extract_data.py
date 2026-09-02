# extract_data.py
import os
from dotenv import load_dotenv

load_dotenv()

import json
import google.genai as genai
import atexit
from extract_text import extract_text_from_pdf  # Your PDF->text function

# --- CONFIGURE API ---
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


def extract_invoice_data(pdf_path):
    # Step 1: Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    # Step 2: Build prompt for AI
    prompt = f"""
    Extract the client name, invoice amount, and product name from the invoice text
    and return it as a JSON object with keys: client_name, invoice_amount, product_name.
    If a value is missing, return null.
    Invoice text:
    {text}
    """

    # Step 3: Generate content using Gemini 2.5
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Step 4: Parse JSON output
    try:
        output_text = response.text.strip()
        # Extract JSON from AI response
        json_start = output_text.find('{')
        json_end = output_text.rfind('}') + 1
        json_data = json.loads(output_text[json_start:json_end])
        # Add PDF filename for reference
        json_data["pdf_file"] = pdf_path
        return json_data
    except Exception as e:
        print("Failed to parse AI output:", e)
        return None

# --- Test run ---
if __name__ == "__main__":
    pdf_file = "sample_invoice.pdf"  # Make sure this file exists
    data = extract_invoice_data(pdf_file)
    print(data)


@atexit.register
def shutdown():
    try:
        client.close()
    except Exception:
        pass
