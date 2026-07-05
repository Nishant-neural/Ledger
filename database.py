"""
database.py - Handles all SQLite storage for the Ledger app.
Fully offline - creates a local file called ledger.db in the same folder.
"""
import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.db")


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            party TEXT,
            category TEXT,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    # seed some common categories if empty
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        defaults = ["Sales", "Purchases", "Rent", "Salary", "Utilities",
                    "Transport", "Misc Income", "Misc Expense"]
        cur.executemany("INSERT INTO categories (name) VALUES (?)",
                         [(d,) for d in defaults])
    conn.commit()
    conn.close()


def add_transaction(date, party, category, description, debit, credit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (date, party, category, description, debit, credit)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, party, category, description, debit or 0, credit or 0))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def update_transaction(tid, date, party, category, description, debit, credit):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE transactions
        SET date=?, party=?, category=?, description=?, debit=?, credit=?
        WHERE id=?
    """, (date, party, category, description, debit or 0, credit or 0, tid))
    conn.commit()
    conn.close()


def delete_transaction(tid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def get_transactions(search_text="", category="", date_from="", date_to=""):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if search_text:
        query += " AND (party LIKE ? OR description LIKE ?)"
        params += [f"%{search_text}%", f"%{search_text}%"]
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    query += " ORDER BY date ASC, id ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM categories ORDER BY name ASC")
    rows = [r["name"] for r in cur.fetchall()]
    conn.close()
    return rows


def add_category(name):
    if not name:
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_summary():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(credit),0) as total_credit, COALESCE(SUM(debit),0) as total_debit FROM transactions")
    row = cur.fetchone()
    conn.close()
    total_credit = row["total_credit"]
    total_debit = row["total_debit"]
    return total_credit, total_debit, (total_credit - total_debit)


def clear_all_transactions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
