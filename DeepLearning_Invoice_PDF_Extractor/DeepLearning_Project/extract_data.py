# extract_data.py
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current folder, parent, or project root
current_dir = Path(__file__).resolve().parent
load_dotenv(current_dir / ".env")
load_dotenv(current_dir.parent / ".env")

from extract_text import extract_text_from_pdf

def get_groq_key():
    return os.getenv("GROQ_API_KEY")

def get_gemini_key():
    return os.getenv("GEMINI_API_KEY")


def _extract_with_groq(prompt: str, api_key: str, model: str = "openai/gpt-oss-20b"):
    """Query Groq API with given model."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert financial and invoice data extraction model. Extract information accurately and return strictly a valid JSON object matching the requested schema."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )
        return response.choices[0].message.content, None
    except Exception as e:
        err_msg = f"Groq API error ({model}): {e}"
        print(err_msg)
        return None, err_msg


def _extract_with_gemini(prompt: str, api_key: str, model: str = "gemini-2.5-flash"):
    """Query Google Gemini API."""
    try:
        import google.genai as genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text, None
    except Exception as e:
        err_msg = f"Gemini API error ({model}): {e}"
        print(err_msg)
        return None, err_msg


def _clean_and_parse_json(raw_text: str):
    """Extract and parse JSON safely from model response."""
    if not raw_text:
        return None, "Empty model output received."

    cleaned = raw_text.strip()
    # Remove markdown code blocks if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)

    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0)), None
        except json.JSONDecodeError as err:
            print(f"JSON decode failed on matched block: {err}")

    try:
        return json.loads(cleaned), None
    except Exception as err:
        return None, f"Failed to parse raw output as JSON: {err}"


def _clean_numeric(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = re.sub(r"[^\d.]", "", val)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return None


def extract_invoice_data(pdf_source, filename="invoice.pdf", preferred_model="openai/gpt-oss-20b"):
    """
    Extracts rich invoice details (invoice_number, dates, party names, taxes, totals, line items).
    Returns (data_dict, error_message).
    """
    text = extract_text_from_pdf(pdf_source)
    if not text:
        err = f"No text could be extracted from PDF: {filename}"
        print(err)
        return None, err

    prompt = f"""
Analyze the following invoice text and extract key metadata.
Return ONLY a valid JSON object matching this exact schema:
{{
    "invoice_number": string or null,
    "invoice_date": "YYYY-MM-DD" or null,
    "due_date": "YYYY-MM-DD" or null,
    "client_name": string or null,
    "vendor_name": string or null,
    "product_name": string or null,
    "tax_amount": numeric float or null,
    "invoice_amount": numeric float or null,
    "currency": "USD" or "INR" or "EUR" or string or null,
    "status": "Paid" or "Pending" or "Overdue",
    "line_items": [
        {{
            "description": string,
            "quantity": numeric float,
            "unit_price": numeric float,
            "total": numeric float
        }}
    ],
    "notes": string or null
}}

Invoice text:
\"\"\"
{text}
\"\"\"
"""

    groq_key = get_groq_key()
    gemini_key = get_gemini_key()
    raw_output = None
    last_error = None

    if groq_key:
        raw_output, last_error = _extract_with_groq(prompt, groq_key, model=preferred_model)

    if not raw_output and gemini_key:
        raw_output, last_error = _extract_with_gemini(prompt, gemini_key, model="gemini-2.5-flash")

    if not raw_output:
        msg = last_error or "No AI response received. Please check GROQ_API_KEY or GEMINI_API_KEY in .env."
        print(f"Error: {msg}")
        return None, msg

    data, parse_err = _clean_and_parse_json(raw_output)
    if data and isinstance(data, dict):
        # Normalize fields
        data["invoice_amount"] = _clean_numeric(data.get("invoice_amount"))
        data["tax_amount"] = _clean_numeric(data.get("tax_amount"))
        if not data.get("currency"):
            data["currency"] = "USD"
        if not data.get("status"):
            data["status"] = "Pending"
        if not isinstance(data.get("line_items"), list):
            data["line_items"] = []

        if isinstance(pdf_source, (str, os.PathLike)):
            data["pdf_file"] = os.path.basename(pdf_source)
        else:
            data["pdf_file"] = filename

        return data, None

    return None, (parse_err or "Failed to parse structured invoice data.")


if __name__ == "__main__":
    pdf_file = "sample_invoice.pdf"
    if os.path.exists(pdf_file):
        data, err = extract_invoice_data(pdf_file)
        print("Rich Extraction Result:", json.dumps(data, indent=2))
        if err:
            print("Error:", err)
    else:
        print(f"Sample file {pdf_file} not found.")
