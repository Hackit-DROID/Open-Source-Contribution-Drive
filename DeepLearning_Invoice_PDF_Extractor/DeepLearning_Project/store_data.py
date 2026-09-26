# store_data.py
import os
import json
import sqlite3
from pathlib import Path
from extract_data import extract_invoice_data

DB_PATH = Path(__file__).resolve().parent / "invoices.db"


def init_db(db_path=DB_PATH):
    """Initialize invoices database table with rich schema columns."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        filename TEXT PRIMARY KEY,
        invoice_number TEXT,
        invoice_date TEXT,
        due_date TEXT,
        client_name TEXT,
        vendor_name TEXT,
        invoice_amount REAL,
        tax_amount REAL,
        currency TEXT DEFAULT 'USD',
        product_name TEXT,
        status TEXT DEFAULT 'Pending',
        line_items_json TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)
    conn.commit()

    # Migration: Check for newly added columns if table existed prior
    cursor.execute("PRAGMA table_info(invoices)")
    existing_cols = {col[1] for col in cursor.fetchall()}
    new_cols = {
        "invoice_number": "TEXT",
        "invoice_date": "TEXT",
        "due_date": "TEXT",
        "vendor_name": "TEXT",
        "tax_amount": "REAL",
        "currency": "TEXT DEFAULT 'USD'",
        "status": "TEXT DEFAULT 'Pending'",
        "line_items_json": "TEXT",
        "notes": "TEXT",
        "created_at": "TEXT"
    }
    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Column migration notice for {col_name}: {e}")

    conn.commit()
    conn.close()


def store_invoice(pdf_source, filename="invoice.pdf", db_path=DB_PATH, model="openai/gpt-oss-20b"):
    """
    Extracts rich invoice data and persists/updates it in SQLite.
    Returns (data_dict, error_message).
    """
    init_db(db_path)
    data, err = extract_invoice_data(pdf_source, filename=filename, preferred_model=model)
    if not data:
        return None, err

    final_name = data.get("pdf_file", filename)
    line_items_str = json.dumps(data.get("line_items", []))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invoices (
        filename, invoice_number, invoice_date, due_date, client_name,
        vendor_name, invoice_amount, tax_amount, currency, product_name,
        status, line_items_json, notes
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(filename) DO UPDATE SET
        invoice_number=excluded.invoice_number,
        invoice_date=excluded.invoice_date,
        due_date=excluded.due_date,
        client_name=excluded.client_name,
        vendor_name=excluded.vendor_name,
        invoice_amount=excluded.invoice_amount,
        tax_amount=excluded.tax_amount,
        currency=excluded.currency,
        product_name=excluded.product_name,
        status=excluded.status,
        line_items_json=excluded.line_items_json,
        notes=excluded.notes
    """, (
        final_name,
        data.get("invoice_number"),
        data.get("invoice_date"),
        data.get("due_date"),
        data.get("client_name"),
        data.get("vendor_name"),
        data.get("invoice_amount"),
        data.get("tax_amount"),
        data.get("currency", "USD"),
        data.get("product_name"),
        data.get("status", "Pending"),
        line_items_str,
        data.get("notes")
    ))
    conn.commit()
    conn.close()
    return data, None


def update_invoice_record(filename, updated_fields: dict, db_path=DB_PATH):
    """Update fields directly in SQLite for human-in-the-loop editing."""
    init_db(db_path)
    allowed_cols = {
        "invoice_number", "invoice_date", "due_date", "client_name",
        "vendor_name", "invoice_amount", "tax_amount", "currency",
        "product_name", "status", "notes"
    }
    set_clauses = []
    values = []
    for k, v in updated_fields.items():
        if k in allowed_cols:
            set_clauses.append(f"{k} = ?")
            values.append(v)

    if not set_clauses:
        return False

    values.append(filename)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"UPDATE invoices SET {', '.join(set_clauses)} WHERE filename = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()
    return True


def delete_invoice_record(filename, db_path=DB_PATH):
    """Delete an invoice record from SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    current_dir = Path(__file__).resolve().parent
    sample_pdf = current_dir / "sample_invoice.pdf"
    if sample_pdf.exists():
        data, err = store_invoice(str(sample_pdf), filename="sample_invoice.pdf")
        print("Stored Sample Data:", data)
