import sqlite3
from extract_data import extract_invoice_data
import os

DB_NAME = "invoices.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        filename TEXT PRIMARY KEY,
        client_name TEXT,
        invoice_amount REAL,
        product_name TEXT
    )
    """)
    conn.commit()
    conn.close()

def store_invoice(pdf_path):
    data = extract_invoice_data(pdf_path)
    if not data:  # Skip if extraction failed
        print(f"Skipping {pdf_path}, no data extracted.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invoices (filename, client_name, invoice_amount, product_name)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(filename) DO UPDATE SET
        client_name=excluded.client_name,
        invoice_amount=excluded.invoice_amount,
        product_name=excluded.product_name
    """, (data["pdf_file"], data["client_name"], data["invoice_amount"], data["product_name"]))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

    # Put invoices inside this folder
    folder = r"C:\Users\hp\OneDrive\Desktop\VACATION\Django\DeepLearning_Project\invoices"

    # Make sure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created empty folder: {folder} (add PDFs here)")

    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            store_invoice(os.path.join(folder, file))

    print("All invoices processed and stored in database.")
