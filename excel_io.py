"""
excel_io.py - Import transactions from an Excel sheet and export the ledger to Excel.
Uses openpyxl only (no pandas dependency needed).
"""
import openpyxl
from datetime import datetime
import database as db

# Column names we try to auto-detect in the uploaded Excel sheet.
# The matching is case-insensitive and flexible on naming.
COLUMN_ALIASES = {
    "date": ["date", "transaction date", "txn date"],
    "party": ["party", "name", "customer", "vendor", "payee", "client"],
    "category": ["category", "type", "head", "account"],
    "description": ["description", "details", "narration", "remarks", "note"],
    "debit": ["debit", "expense", "paid", "out", "withdrawal"],
    "credit": ["credit", "income", "received", "in", "deposit"],
}


def _normalize(text):
    return str(text).strip().lower() if text is not None else ""


def detect_columns(header_row):
    """
    Given the header row (list of cell values), figure out which column index
    maps to which field (date, party, category, description, debit, credit).
    Returns a dict: field_name -> column_index (0-based), or None if not found.
    """
    mapping = {}
    normalized_headers = [_normalize(h) for h in header_row]
    for field, aliases in COLUMN_ALIASES.items():
        found_idx = None
        for idx, header in enumerate(normalized_headers):
            if header in aliases:
                found_idx = idx
                break
        mapping[field] = found_idx
    return mapping


def read_excel_preview(filepath, max_rows=5):
    """Read the header row and a few preview rows for user confirmation."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    header = list(rows[0])
    preview = [list(r) for r in rows[1:1 + max_rows]]
    return header, preview


def import_excel(filepath, column_mapping=None):
    """
    Import transactions from an Excel file into the ledger database.
    column_mapping: optional dict overriding auto-detected columns,
                    e.g. {"date": 0, "party": 1, "debit": 4, "credit": 5}
    Returns (success_count, error_count, error_messages)
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return 0, 0, ["The sheet appears to be empty."]

    header = list(rows[0])
    data_rows = rows[1:]

    mapping = column_mapping if column_mapping else detect_columns(header)

    if mapping.get("date") is None:
        return 0, 0, ["Could not find a 'Date' column. Please map columns manually."]

    success, errors = 0, []
    for i, row in enumerate(data_rows, start=2):  # row 2 = first data row (1-indexed in Excel)
        try:
            date_val = row[mapping["date"]] if mapping.get("date") is not None else None
            if date_val is None or str(date_val).strip() == "":
                continue  # skip blank rows

            if isinstance(date_val, datetime):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val).strip()

            party = str(row[mapping["party"]]).strip() if mapping.get("party") is not None and row[mapping["party"]] is not None else ""
            category = str(row[mapping["category"]]).strip() if mapping.get("category") is not None and row[mapping["category"]] is not None else "Misc Expense"
            description = str(row[mapping["description"]]).strip() if mapping.get("description") is not None and row[mapping["description"]] is not None else ""

            debit = row[mapping["debit"]] if mapping.get("debit") is not None else 0
            credit = row[mapping["credit"]] if mapping.get("credit") is not None else 0
            debit = float(debit) if debit not in (None, "") else 0.0
            credit = float(credit) if credit not in (None, "") else 0.0

            db.add_transaction(date_str, party, category, description, debit, credit)
            if category:
                db.add_category(category)
            success += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return success, len(errors), errors


def export_excel(filepath, rows):
    """Export a list of transaction rows (sqlite3.Row objects) to an Excel file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ledger"
    headers = ["Date", "Party", "Category", "Description", "Debit", "Credit", "Balance"]
    ws.append(headers)

    running_balance = 0.0
    for r in rows:
        running_balance += (r["credit"] or 0) - (r["debit"] or 0)
        ws.append([
            r["date"], r["party"], r["category"], r["description"],
            r["debit"], r["credit"], round(running_balance, 2)
        ])

    # basic column widths
    widths = [12, 20, 16, 30, 10, 10, 12]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    wb.save(filepath)
