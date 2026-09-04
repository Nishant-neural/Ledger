"""
database.py - Handles all SQLite storage for the Ledger app.
Fully offline - creates a local file called ledger.db in the same folder.
"""
import sqlite3
import os
from pathlib import Path

APP_NAME = "SimpleLedger"

APP_DATA_DIR = Path(
    os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")
) / APP_NAME

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = str(APP_DATA_DIR / "ledger.db")


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
    existing_columns = {row[1] for row in cur.execute("PRAGMA table_info(transactions)")}
    for column, definition in {
        "item": "TEXT DEFAULT ''",
        "stock": "REAL DEFAULT 0",
        "buying_rate": "REAL DEFAULT 0",
        "selling_rate": "REAL DEFAULT 0",
    }.items():
        if column not in existing_columns:
            cur.execute(f"ALTER TABLE transactions ADD COLUMN {column} {definition}")
    defaults = ["Sales", "Purchases", "Payment In", "Payment Out", "Rent",
                "Salary", "Utilities", "Transport", "Misc Income", "Misc Expense"]
    cur.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)",
                    [(d,) for d in defaults])
    conn.commit()
    conn.close()


def add_transaction(date, party, category, description, debit, credit,
                    item="", stock=0, buying_rate=0, selling_rate=0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                INSERT INTO transactions
                (date, party, category, description, debit, credit, item, stock, buying_rate, selling_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date, party, category, description, debit or 0, credit or 0,
                    item or "", stock or 0, buying_rate or 0, selling_rate or 0))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def update_transaction(tid, date, party, category, description, debit, credit,
                       item="", stock=0, buying_rate=0, selling_rate=0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE transactions
                SET date=?, party=?, category=?, description=?, debit=?, credit=?,
                        item=?, stock=?, buying_rate=?, selling_rate=?
        WHERE id=?
        """, (date, party, category, description, debit or 0, credit or 0,
                    item or "", stock or 0, buying_rate or 0, selling_rate or 0, tid))
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
        query += " AND (party LIKE ? OR item LIKE ? OR description LIKE ?)"
        params += [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]
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


def get_summary(date_from="", date_to=""):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT COALESCE(SUM(credit),0) as total_credit, COALESCE(SUM(debit),0) as total_debit FROM transactions WHERE 1=1"
    params = []
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    total_credit = row["total_credit"]
    total_debit = row["total_debit"]
    return total_credit, total_debit, (total_credit - total_debit)


def get_sales_summary(month=""):
    """Return item sales, purchase cost, and quantity for an optional YYYY-MM."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT COALESCE(SUM(stock * selling_rate), 0) AS total_sales,
               COALESCE(SUM(stock * buying_rate), 0) AS total_purchase,
               COALESCE(SUM(stock), 0) AS total_stock
        FROM transactions
        WHERE stock > 0
    """
    params = []
    if month:
        query += " AND substr(date, 1, 7) = ?"
        params.append(month)
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row["total_sales"], row["total_purchase"], row["total_stock"]


def get_party_balances():
    """Return debit/credit totals and net balance for every party."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT party,
               COALESCE(SUM(debit), 0) AS total_debit,
               COALESCE(SUM(credit), 0) AS total_credit,
               COALESCE(SUM(credit - debit), 0) AS net_balance
        FROM transactions
        WHERE TRIM(COALESCE(party, '')) != ''
        GROUP BY party
        ORDER BY ABS(net_balance) DESC, party ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_cashbook(date_from="", date_to=""):
    """Return day-wise cash in, cash out, and running balance."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT date,
               COALESCE(SUM(credit), 0) AS cash_in,
               COALESCE(SUM(debit), 0) AS cash_out
        FROM transactions
        WHERE 1=1
    """
    params = []
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    query += " GROUP BY date ORDER BY date ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    running = 0.0
    cashbook = []
    for row in rows:
        cash_in = row["cash_in"] or 0
        cash_out = row["cash_out"] or 0
        running += cash_in - cash_out
        cashbook.append({
            "date": row["date"],
            "cash_in": cash_in,
            "cash_out": cash_out,
            "net": cash_in - cash_out,
            "running_balance": running,
        })
    return cashbook


def get_inventory_report():
    """Return item-wise purchased, sold, available stock, value, and profit."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT item, category, stock, buying_rate, selling_rate
        FROM transactions
        WHERE TRIM(COALESCE(item, '')) != ''
    """)
    rows = cur.fetchall()
    conn.close()

    items = {}
    for row in rows:
        item_name = row["item"] or ""
        data = items.setdefault(item_name, {
            "item": item_name,
            "purchased_qty": 0.0,
            "sold_qty": 0.0,
            "purchase_value": 0.0,
            "sales_value": 0.0,
            "sales_cost": 0.0,
        })
        category = (row["category"] or "").strip().lower()
        qty = row["stock"] or 0
        buying_rate = row["buying_rate"] or 0
        selling_rate = row["selling_rate"] or 0
        if category == "purchases":
            data["purchased_qty"] += qty
            data["purchase_value"] += qty * buying_rate
        elif category == "sales":
            data["sold_qty"] += qty
            data["sales_value"] += qty * selling_rate
            data["sales_cost"] += qty * buying_rate

    report = []
    for data in items.values():
        avg_cost = (
            data["purchase_value"] / data["purchased_qty"]
            if data["purchased_qty"] else 0.0
        )
        fallback_cost = data["sold_qty"] * avg_cost
        cost_of_sales = data["sales_cost"] or fallback_cost
        available_qty = data["purchased_qty"] - data["sold_qty"]
        report.append({
            **data,
            "available_qty": available_qty,
            "avg_cost": avg_cost,
            "stock_value": available_qty * avg_cost,
            "gross_profit": data["sales_value"] - cost_of_sales,
        })
    return sorted(report, key=lambda r: (r["available_qty"], r["item"].lower()))


def get_low_stock_items(limit=5):
    """Return inventory rows at or below the requested available quantity."""
    return [row for row in get_inventory_report() if row["available_qty"] <= limit]


def clear_all_transactions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
