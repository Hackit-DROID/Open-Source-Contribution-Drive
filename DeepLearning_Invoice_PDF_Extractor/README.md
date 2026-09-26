# DeepLearning Invoice Extractor Pro 🧾

An end-to-end open-source solution for automated invoice data extraction using deep learning OCR fallbacks, high-speed LLM reasoning (Groq / Google Gemini), SQLite persistence with schema migration, human-in-the-loop review, and executive financial dashboards.

---

## 🌟 Advanced Features Implemented

1. **Rich Invoice Schema Extraction**:
   - **Identifiers & Dates**: `invoice_number`, `invoice_date`, `due_date`.
   - **Parties**: `client_name`, `vendor_name`.
   - **Financials**: Subtotals, `tax_amount`, `invoice_amount`, `currency` (USD/INR/EUR), and payment `status` (Pending/Paid/Overdue).
   - **Line Items**: Individual product breakdowns (`description`, `quantity`, `unit_price`, `total`).

2. **Multi-Model LLM Selector**:
   - Choose your preferred model directly from the sidebar:
     - Groq: `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-120b`
     - Gemini: `gemini-2.5-flash`

3. **Human-in-the-Loop Review & Corrections**:
   - Dedicated **"Review & Edit Invoices"** tab to inspect, correct, and update misread or missing fields directly into the database.
   - Delete obsolete invoices or update payment statuses (`Pending`, `Paid`, `Overdue`).

4. **Executive Financial Analytics & Charts**:
   - Executive KPI cards: Total Invoices, Total Spend, Average Invoice, Total Tax/VAT, Pending vs. Paid vs. Overdue counts.
   - Interactive Plotly visualizations:
     - Total Spend by Client (Bar Chart)
     - Spend Share Distribution (Donut Chart)
     - Monthly Spend Timeline (Line Trend Chart)

5. **Multi-Format Export**:
   - **CSV Export**: Standard flat invoice export.
   - **Multi-Sheet Excel (`.xlsx`) Export**: Generates an Excel workbook containing:
     - Sheet 1: `Invoices`
     - Sheet 2: `Client Breakdown`
     - Sheet 3: `Monthly Trends`

6. **Robust Extraction Pipeline**:
   - Supports file paths, byte streams, and in-memory buffers (no temp file locks on Windows).
   - Automatic fallback to OCR (`easyocr`) for scanned invoices.

---

## 📂 Project Architecture

```text
DeepLearning_Invoice_PDF_Extractor/
├── .env.example                       # API key template
├── .env                               # Local secrets (Groq / Gemini)
├── README.md                          # Project documentation
└── DeepLearning_Project/
    ├── app.py                         # Streamlit multi-tab web application
    ├── extract_text.py                # Digital PDF & OCR extraction
    ├── extract_data.py                # LLM reasoning with rich JSON schema
    ├── store_data.py                  # SQLite schema, migration & CRUD helpers
    ├── reports.py                     # Financial aggregations & timeline metrics
    ├── sample_invoice.pdf             # Test PDF invoice
    ├── invoices.db                    # SQLite database
    └── requirements.txt               # Updated dependency specifications
```

---

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Create a `.env` file in the root or `DeepLearning_Project/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   # or
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```
   Open **`http://localhost:8501`** in your browser.
