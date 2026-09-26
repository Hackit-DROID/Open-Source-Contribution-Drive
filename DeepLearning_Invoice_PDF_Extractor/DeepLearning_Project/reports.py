# reports.py
import sqlite3
import json
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "invoices.db"


def overall_summary(db_path=DB_PATH):
    """Returns comprehensive invoice metrics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*), 
            COALESCE(SUM(invoice_amount), 0.0),
            COALESCE(AVG(invoice_amount), 0.0),
            COUNT(DISTINCT client_name),
            COALESCE(SUM(tax_amount), 0.0),
            SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END)
        FROM invoices
    """)
    row = cursor.fetchone()
    conn.close()

    count, total, avg_amt, unique_clients, total_tax, paid, pending, overdue = row if row else (0, 0.0, 0.0, 0, 0.0, 0, 0, 0)
    return {
        "total_invoices": count or 0,
        "total_amount": round(total or 0.0, 2),
        "average_amount": round(avg_amt or 0.0, 2),
        "unique_clients": unique_clients or 0,
        "total_tax": round(total_tax or 0.0, 2),
        "paid_count": paid or 0,
        "pending_count": pending or 0,
        "overdue_count": overdue or 0,
    }


def client_breakdown(db_path=DB_PATH):
    """Returns aggregate spent and status counts per client."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(client_name, 'Unknown') AS client, 
            COUNT(*) AS invoice_count,
            ROUND(COALESCE(SUM(invoice_amount), 0.0), 2) AS total_spent,
            ROUND(COALESCE(AVG(invoice_amount), 0.0), 2) AS avg_spent
        FROM invoices 
        GROUP BY client_name
        ORDER BY total_spent DESC
    """)
    results = cursor.fetchall()
    conn.close()
    return [
        {
            "client_name": row[0],
            "invoice_count": row[1],
            "total_spent": row[2],
            "avg_spent": row[3]
        }
        for row in results
    ]


def monthly_trends(db_path=DB_PATH):
    """Returns monthly invoice amounts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            SUBSTR(COALESCE(invoice_date, 'Unknown'), 1, 7) AS month,
            COUNT(*) AS invoice_count,
            ROUND(COALESCE(SUM(invoice_amount), 0.0), 2) AS total_amount
        FROM invoices
        GROUP BY month
        ORDER BY month ASC
    """)
    results = cursor.fetchall()
    conn.close()
    return [
        {"month": row[0], "invoice_count": row[1], "total_amount": row[2]}
        for row in results if row[0] != 'Unknown'
    ]


def get_all_invoices(db_path=DB_PATH):
    """Fetch all stored invoices with extended fields."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            filename, invoice_number, invoice_date, due_date, client_name,
            vendor_name, invoice_amount, tax_amount, currency, product_name,
            status, line_items_json, notes
        FROM invoices 
        ORDER BY invoice_date DESC, filename ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "filename": r[0],
            "invoice_number": r[1],
            "invoice_date": r[2],
            "due_date": r[3],
            "client_name": r[4],
            "vendor_name": r[5],
            "invoice_amount": r[6],
            "tax_amount": r[7],
            "currency": r[8] or "USD",
            "product_name": r[9],
            "status": r[10] or "Pending",
            "line_items_json": r[11],
            "notes": r[12]
        }
        for r in rows
    ]


if __name__ == "__main__":
    print("--- Summary ---")
    print(overall_summary())
    print("\n--- Client Breakdown ---")
    print(client_breakdown())
    print("\n--- Monthly Trends ---")
    print(monthly_trends())
