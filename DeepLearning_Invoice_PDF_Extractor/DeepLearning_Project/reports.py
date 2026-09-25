import sqlite3

DB_NAME = "invoices.db"

def overall_summary():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(invoice_amount) FROM invoices")
    count, total = cursor.fetchone()
    conn.close()
    return {"total_invoices": count, "total_amount": total}

def client_breakdown():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT client_name, SUM(invoice_amount) FROM invoices GROUP BY client_name")
    results = cursor.fetchall()
    conn.close()
    return [{"client_name": row[0], "total_spent": row[1]} for row in results]

if __name__ == "__main__":
    print("Overall Summary:", overall_summary())
    print("Client Breakdown:", client_breakdown())
