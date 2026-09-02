# extract_text.py
from pypdf import PdfReader
import easyocr
import os
pdf_path = "sample_invoice.pdf"
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from PDF. Automatically uses OCR if needed.
    """
    text = ""
    try:
        # Try pypdf first (works for text PDFs)
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"pypdf failed: {e}")

    # If text is empty, use OCR (scanned PDFs)
    if not text.strip():
        print("Using OCR for scanned PDF...")
        reader = easyocr.Reader(['en'])
        results = reader.readtext(pdf_path, detail=0)
        text = "\n".join(results)

    return text
