# extract_text.py
import os
import io
from pypdf import PdfReader


def extract_text_from_pdf(pdf_source):
    """
    Extracts text from PDF using pypdf.
    Accepts a file path (str/Path), bytes, or a file-like stream (io.BytesIO).
    Gracefully falls back to OCR (easyocr) if available when PDF is scanned.
    """
    text = ""
    try:
        if isinstance(pdf_source, (str, os.PathLike)):
            if not os.path.exists(pdf_source):
                raise FileNotFoundError(f"PDF file not found: {pdf_source}")
            reader = PdfReader(pdf_source)
        elif isinstance(pdf_source, bytes):
            reader = PdfReader(io.BytesIO(pdf_source))
        else:
            # File-like object (e.g. Streamlit UploadedFile)
            pdf_source.seek(0)
            reader = PdfReader(pdf_source)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"pypdf extraction warning: {e}")

    # Fallback to OCR if extracted text is blank and easyocr is installed
    if not text.strip() and isinstance(pdf_source, (str, os.PathLike)):
        try:
            import easyocr  # type: ignore
            print("pypdf found no text. Attempting OCR with easyocr...")
            reader = easyocr.Reader(['en'])
            results = reader.readtext(pdf_source, detail=0)
            text = "\n".join(results)
        except ImportError:
            print("Note: easyocr is not installed. To extract text from scanned/image PDFs, install easyocr.")
        except Exception as ocr_err:
            print(f"OCR extraction failed: {ocr_err}")

    return text.strip()


if __name__ == "__main__":
    sample_file = "sample_invoice.pdf"
    if os.path.exists(sample_file):
        extracted = extract_text_from_pdf(sample_file)
        print("--- Extracted Text ---")
        print(extracted)
    else:
        print(f"File {sample_file} not found.")
