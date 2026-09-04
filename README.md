# Simple Ledger — Offline Desktop Ledger App

A lightweight, fully offline ledger app for small businesses. No internet
connection, cloud account, or subscription needed. All your data is stored
locally in a single file (`ledger.db`) right next to the app.

## Features
- Add, edit, and delete income/expense transactions
- Import transactions directly from an Excel sheet (`.xlsx`)
- Export your full ledger to Excel anytime
- Search by party/description, filter by category or date range
- Live totals: Total Income, Total Expense, Net Balance, Total Sales, and monthly sales
- Item tracking: item name, stock/quantity, buying rate, selling rate, and calculated sales
- Simple, clean interface — no training needed

---

## SME helper features
- Inventory report with purchased, sold, available stock, stock value, sales value, and gross profit by item
- Low-stock report for items with 5 or fewer units available
- Party balances showing total credit, total debit, net balance, and receivable/payable status
- Daily cashbook showing cash in, cash out, net change, and running balance by date
- Quick entry presets for Sale, Purchase, Payment In, and Payment Out
- Excel export now includes Ledger, Daily Cashbook, Party Balances, Inventory, and Low Stock sheets

---

## 1. One-time setup

You need **Python 3.9+** installed (Windows/macOS/Linux all work).

**Check if you already have it** — open a terminal / command prompt and run:
```
python3 --version
```
If that fails, try `python --version`. If neither works, download Python
from https://www.python.org/downloads/ and during installation on Windows,
make sure you tick **"Add Python to PATH"**.

**Windows only note:** Tkinter (the GUI toolkit) comes bundled with the
official Python installer, so nothing extra is needed there.
**Linux only note:** if you get a `No module named tkinter` error, install it with:
```
sudo apt-get install python3-tk
```

**Install the one dependency** (openpyxl, used for Excel import/export):
```
pip install -r requirements.txt
```

---

## 2. Running the app

From inside the `ledger_app` folder, run:
```
python3 main.py
```
(or `python main.py` on Windows)

A window will open — that's it. The app creates `ledger.db` in this same
folder the first time you run it. That file holds all your data. Back it up
occasionally (just copy the file) since it's the only copy of your records.

---

## 3. Using the app

### Adding a transaction
Fill in the form at the bottom (Date, Item, Stock/Qty, Buying rate, Selling
rate, Party, Category, and Description) and click **Add Transaction**. Total
sales is calculated as `Stock/Qty × Selling rate`; purchase cost is calculated
as `Stock/Qty × Buying rate`. For the `Sales` category, the calculated sales
amount fills Credit automatically. For `Purchases`, the calculated purchase
cost fills Debit automatically.

### Editing / deleting
Click any row in the table — it loads into the form. Change values and
click **Update Selected**, or click **Delete Selected** to remove it.

### Importing from Excel
Click **📥 Import from Excel** and choose your `.xlsx` file. The app tries
to auto-detect columns named things like `Date`, `Party`, `Category`,
`Description`, `Debit`, `Credit` (case-insensitive, some common synonyms
like "Vendor", "Income", "Expense" are also recognized). If it can't detect
your columns automatically, a popup lets you manually match each column.

### Exporting to Excel
Click **📤 Export to Excel** to save your entire ledger — including a
running balance column — as a new `.xlsx` file you can open in Excel or
Google Sheets.

### Searching & filtering
Use the search box (matches Item, Party, or Description), the Category
dropdown, and the From/To date fields (format: `YYYY-MM-DD`) to narrow the
table. Enter a month as `YYYY-MM` in **Sales month** to see that month's
calculated item sales. Existing databases are upgraded automatically without
deleting their old transactions.

---

## 4. Files in this folder
| File | Purpose |
|---|---|
| `main.py` | The app itself — run this |
| `database.py` | Local SQLite storage logic |
| `excel_io.py` | Excel import/export logic |
| `ledger.db` | Your data (created automatically on first run) |
| `requirements.txt` | The one Python package needed |

## 5. Optional: turning this into a single .exe (Windows)
If you'd like a double-click `.exe` with no terminal needed, install
PyInstaller and run:
```
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```
The `.exe` will appear in the `dist` folder. Copy `ledger.db` (or let it
regenerate) next to the `.exe` when you run it.
