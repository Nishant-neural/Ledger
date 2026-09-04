"""
Simple Ledger - offline desktop ledger app for small businesses.
Run with: python main.py

Features:
- Add / edit / delete transactions (income & expense)
- Import transactions straight from an Excel sheet
- Export the whole ledger to Excel
- Search & filter by party/description, category, date range
- Running totals: total income, total expense, net balance
- 100% offline - all data stored locally in ledger.db (SQLite)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

import database as db
import excel_io

APP_BG = "#f4f6f8"
HEADER_BG = "#1f6f5c"
ACCENT = "#1f6f5c"
DANGER = "#c0392b"
FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SUMMARY = ("Segoe UI", 12, "bold")


class LedgerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Ledger — Offline Business Ledger")
        self.geometry("1080x680")
        self.minsize(900, 560)
        self.configure(bg=APP_BG)

        db.init_db()
        self.selected_id = None

        self._build_header()
        self._build_toolbar()
        self._build_summary_bar()
        self._build_business_tools()
        self._build_table()
        self._build_entry_form()

        self.refresh_table()

    # ---------- UI BUILD ----------
    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, height=60)
        header.pack(fill="x")
        tk.Label(header, text="📒 Simple Ledger", font=FONT_HEADER,
                 bg=HEADER_BG, fg="white", padx=20, pady=14).pack(side="left")
        tk.Label(header, text="Offline • No internet needed • Your data stays on this computer",
                 font=FONT_NORMAL, bg=HEADER_BG, fg="#d7ede6").pack(side="right", padx=20)

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=APP_BG, pady=8)
        bar.pack(fill="x", padx=16)

        tk.Label(bar, text="Search:", bg=APP_BG, font=FONT_NORMAL).pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(bar, textvariable=self.search_var, width=22, font=FONT_NORMAL)
        search_entry.pack(side="left", padx=(4, 12))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        tk.Label(bar, text="Category:", bg=APP_BG, font=FONT_NORMAL).pack(side="left")
        self.filter_category = tk.StringVar(value="All")
        self.filter_cat_combo = ttk.Combobox(bar, textvariable=self.filter_category,
                                              width=16, state="readonly")
        self.filter_cat_combo.pack(side="left", padx=(4, 12))
        self.filter_cat_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        tk.Label(bar, text="From:", bg=APP_BG, font=FONT_NORMAL).pack(side="left")
        self.date_from = tk.Entry(bar, width=11, font=FONT_NORMAL)
        self.date_from.pack(side="left", padx=(4, 8))
        tk.Label(bar, text="To:", bg=APP_BG, font=FONT_NORMAL).pack(side="left")
        self.date_to = tk.Entry(bar, width=11, font=FONT_NORMAL)
        self.date_to.pack(side="left", padx=(4, 8))
        tk.Button(bar, text="Apply", command=self.refresh_table, font=FONT_NORMAL,
                  bg="white", relief="groove").pack(side="left", padx=(0, 16))
        tk.Button(bar, text="Clear filters", command=self.clear_filters, font=FONT_NORMAL,
                  bg="white", relief="groove").pack(side="left")

        tk.Label(bar, text="Sales month:", bg=APP_BG, font=FONT_NORMAL).pack(side="left", padx=(16, 4))
        self.sales_month = tk.Entry(bar, width=8, font=FONT_NORMAL)
        self.sales_month.insert(0, date.today().strftime("%Y-%m"))
        self.sales_month.pack(side="left")
        self.sales_month.bind("<KeyRelease>", lambda e: self.refresh_sales_summary())

        # right side: import/export buttons
        tk.Button(bar, text="📥 Import from Excel", command=self.import_excel,
                  font=FONT_BOLD, bg=ACCENT, fg="white", relief="flat", padx=10, pady=4
                  ).pack(side="right", padx=4)
        tk.Button(bar, text="📤 Export to Excel", command=self.export_excel,
                  font=FONT_BOLD, bg="white", fg=ACCENT, relief="groove", padx=10, pady=4
                  ).pack(side="right", padx=4)

    def _build_summary_bar(self):
        self.summary_frame = tk.Frame(self, bg="white", pady=10)
        self.summary_frame.pack(fill="x", padx=16, pady=(0, 8))

        self.income_label = tk.Label(self.summary_frame, text="Total Income: ₹0.00",
                                      font=FONT_SUMMARY, bg="white", fg="#1f6f5c")
        self.income_label.pack(side="left", padx=20)
        self.expense_label = tk.Label(self.summary_frame, text="Total Expense: ₹0.00",
                                       font=FONT_SUMMARY, bg="white", fg=DANGER)
        self.expense_label.pack(side="left", padx=20)
        self.balance_label = tk.Label(self.summary_frame, text="Net Balance: ₹0.00",
                                       font=FONT_SUMMARY, bg="white", fg="#2c3e50")
        self.balance_label.pack(side="left", padx=20)
        self.sales_label = tk.Label(self.summary_frame, text="Total Sales: ₹0.00",
                        font=FONT_SUMMARY, bg="white", fg="#2980b9")
        self.sales_label.pack(side="left", padx=20)
        self.month_sales_label = tk.Label(self.summary_frame, text="Month Sales: ₹0.00",
                          font=FONT_SUMMARY, bg="white", fg="#8e44ad")
        self.month_sales_label.pack(side="left", padx=20)

    def _build_business_tools(self):
        tools = tk.Frame(self, bg=APP_BG, pady=2)
        tools.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(tools, text="SME tools:", bg=APP_BG, font=FONT_BOLD).pack(side="left", padx=(0, 8))
        tk.Button(tools, text="Inventory", command=self.show_inventory_report,
                  font=FONT_NORMAL, bg="white", fg="#2c3e50", relief="groove", padx=10
                  ).pack(side="left", padx=4)
        tk.Button(tools, text="Low Stock", command=self.show_low_stock_report,
                  font=FONT_NORMAL, bg="white", fg="#2c3e50", relief="groove", padx=10
                  ).pack(side="left", padx=4)
        tk.Button(tools, text="Party Balances", command=self.show_party_balances,
                  font=FONT_NORMAL, bg="white", fg="#2c3e50", relief="groove", padx=10
                  ).pack(side="left", padx=4)
        tk.Button(tools, text="Daily Cashbook", command=self.show_cashbook,
                  font=FONT_NORMAL, bg="white", fg="#2c3e50", relief="groove", padx=10
                  ).pack(side="left", padx=4)

    def _build_table(self):
        table_frame = tk.Frame(self, bg=APP_BG)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        cols = ("id", "date", "item", "party", "category", "stock", "description", "debit", "credit", "sales")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        headings = {"id": "ID", "date": "Date", "item": "Item", "party": "Party", "category": "Category",
                "stock": "Stock", "description": "Description", "debit": "Debit", "credit": "Credit", "sales": "Total Sales"}
        widths = {"id": 40, "date": 90, "item": 130, "party": 140, "category": 110,
              "stock": 70, "description": 220, "debit": 90, "credit": 90, "sales": 100}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w" if c not in ("debit", "credit") else "e")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def _build_entry_form(self):
        form = tk.LabelFrame(self, text="Add / Edit Transaction", font=FONT_BOLD,
                              bg="white", padx=12, pady=10)
        form.pack(fill="x", padx=16, pady=(0, 14))

        self.entries = {}

        row1 = tk.Frame(form, bg="white")
        row1.pack(fill="x", pady=4)

        tk.Label(row1, text="Date:", bg="white", font=FONT_NORMAL, width=8, anchor="w").pack(side="left")
        self.entry_date = tk.Entry(row1, width=14, font=FONT_NORMAL)
        self.entry_date.insert(0, date.today().isoformat())
        self.entry_date.pack(side="left", padx=(0, 14))

        tk.Label(row1, text="Party:", bg="white", font=FONT_NORMAL, width=8, anchor="w").pack(side="left")
        self.entry_party = tk.Entry(row1, width=20, font=FONT_NORMAL)
        self.entry_party.pack(side="left", padx=(0, 14))

        tk.Label(row1, text="Category:", bg="white", font=FONT_NORMAL, width=8, anchor="w").pack(side="left")
        self.entry_category = ttk.Combobox(row1, width=18, font=FONT_NORMAL)
        self.entry_category.pack(side="left", padx=(0, 14))

        row2 = tk.Frame(form, bg="white")
        row2.pack(fill="x", pady=4)

        tk.Label(row2, text="Description:", bg="white", font=FONT_NORMAL, width=10, anchor="w").pack(side="left")
        self.entry_description = tk.Entry(row2, width=40, font=FONT_NORMAL)
        self.entry_description.pack(side="left", padx=(0, 14))

        tk.Label(row2, text="Debit:", bg="white", font=FONT_NORMAL, width=6, anchor="w").pack(side="left")
        self.entry_debit = tk.Entry(row2, width=10, font=FONT_NORMAL)
        self.entry_debit.pack(side="left", padx=(0, 14))

        tk.Label(row2, text="Credit:", bg="white", font=FONT_NORMAL, width=6, anchor="w").pack(side="left")
        self.entry_credit = tk.Entry(row2, width=10, font=FONT_NORMAL)
        self.entry_credit.pack(side="left", padx=(0, 14))

        row3 = tk.Frame(form, bg="white")
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="Item:", bg="white", font=FONT_NORMAL, width=10, anchor="w").pack(side="left")
        self.entry_item = tk.Entry(row3, width=20, font=FONT_NORMAL)
        self.entry_item.pack(side="left", padx=(0, 14))
        tk.Label(row3, text="Stock/Qty:", bg="white", font=FONT_NORMAL, width=10, anchor="w").pack(side="left")
        self.entry_stock = tk.Entry(row3, width=9, font=FONT_NORMAL)
        self.entry_stock.pack(side="left", padx=(0, 14))
        tk.Label(row3, text="Buying rate:", bg="white", font=FONT_NORMAL, width=11, anchor="w").pack(side="left")
        self.entry_buying_rate = tk.Entry(row3, width=10, font=FONT_NORMAL)
        self.entry_buying_rate.pack(side="left", padx=(0, 14))
        tk.Label(row3, text="Selling rate:", bg="white", font=FONT_NORMAL, width=11, anchor="w").pack(side="left")
        self.entry_selling_rate = tk.Entry(row3, width=10, font=FONT_NORMAL)
        self.entry_selling_rate.pack(side="left", padx=(0, 14))
        self.calculated_sales_label = tk.Label(row3, text="Sales: ₹0.00 | Purchase: ₹0.00",
                                               bg="white", font=FONT_BOLD, fg="#2980b9")
        self.calculated_sales_label.pack(side="left", padx=8)
        for entry in (self.entry_stock, self.entry_buying_rate, self.entry_selling_rate):
            entry.bind("<KeyRelease>", lambda e: self.refresh_calculated_amounts())
        self.entry_category.bind("<<ComboboxSelected>>", lambda e: self.refresh_calculated_amounts())

        btn_frame = tk.Frame(form, bg="white")
        btn_frame.pack(fill="x", pady=(8, 0))
        tk.Button(btn_frame, text="Sale", command=lambda: self.set_transaction_preset("Sales"),
                  bg="#ecf7fb", fg="#1f618d", font=FONT_NORMAL, relief="groove", padx=12, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Purchase", command=lambda: self.set_transaction_preset("Purchases"),
                  bg="#fef5e7", fg="#935116", font=FONT_NORMAL, relief="groove", padx=12, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Payment In", command=lambda: self.set_transaction_preset("Payment In"),
                  bg="#eafaf1", fg="#1e8449", font=FONT_NORMAL, relief="groove", padx=12, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Payment Out", command=lambda: self.set_transaction_preset("Payment Out"),
                  bg="#fdedec", fg=DANGER, font=FONT_NORMAL, relief="groove", padx=12, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Add Transaction", command=self.add_transaction,
                  bg=ACCENT, fg="white", font=FONT_BOLD, relief="flat", padx=14, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Update Selected", command=self.update_transaction,
                  bg="#2980b9", fg="white", font=FONT_BOLD, relief="flat", padx=14, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_transaction,
                  bg=DANGER, fg="white", font=FONT_BOLD, relief="flat", padx=14, pady=6
                  ).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Clear Form", command=self.clear_form,
                  bg="white", fg="#2c3e50", font=FONT_NORMAL, relief="groove", padx=14, pady=6
                  ).pack(side="left", padx=4)

    # ---------- DATA / LOGIC ----------
    def refresh_categories(self):
        cats = db.get_categories()
        self.entry_category["values"] = cats
        self.filter_cat_combo["values"] = ["All"] + cats
        if self.filter_category.get() == "":
            self.filter_category.set("All")

    def refresh_table(self):
        self.refresh_categories()
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = db.get_transactions(
            search_text=self.search_var.get().strip(),
            category=self.filter_category.get(),
            date_from=self.date_from.get().strip(),
            date_to=self.date_to.get().strip(),
        )
        for r in rows:
            self.tree.insert("", "end", values=(
                r["id"], r["date"], r["item"], r["party"], r["category"],
                f"{r['stock']:.2f}" if r["stock"] else "", r["description"],
                f"{r['debit']:.2f}" if r["debit"] else "",
                f"{r['credit']:.2f}" if r["credit"] else "",
                f"{(r['stock'] or 0) * (r['selling_rate'] or 0):.2f}" if r["stock"] and r["selling_rate"] else "",
            ))

        total_credit, total_debit, balance = db.get_summary(
            self.date_from.get().strip(), self.date_to.get().strip())
        self.income_label.config(text=f"Total Income: ₹{total_credit:,.2f}")
        self.expense_label.config(text=f"Total Expense: ₹{total_debit:,.2f}")
        self.balance_label.config(text=f"Net Balance: ₹{balance:,.2f}")
        self.refresh_sales_summary()

    def refresh_sales_summary(self):
        month = self.sales_month.get().strip()
        total_sales, total_purchase, total_stock = db.get_sales_summary()
        month_sales, _, _ = db.get_sales_summary(month)
        self.sales_label.config(text=f"Total Sales: ₹{total_sales:,.2f}")
        self.month_sales_label.config(text=f"{month or 'Month'} Sales: ₹{month_sales:,.2f}")

    def clear_filters(self):
        self.search_var.set("")
        self.filter_category.set("All")
        self.date_from.delete(0, "end")
        self.date_to.delete(0, "end")
        self.refresh_table()

    def set_transaction_preset(self, category):
        self.entry_category.set(category)
        if category == "Payment In":
            self.entry_debit.delete(0, "end")
        elif category == "Payment Out":
            self.entry_credit.delete(0, "end")
        self.refresh_calculated_amounts()

    def _format_money(self, value):
        return f"₹{(value or 0):,.2f}"

    def _format_qty(self, value):
        return f"{(value or 0):,.2f}"

    def _show_report_window(self, title, columns, headings, widths, rows, empty_message):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("920x460")
        win.configure(bg=APP_BG)

        tk.Label(win, text=title, font=FONT_HEADER, bg=APP_BG, fg="#2c3e50",
                 padx=16, pady=12).pack(anchor="w")

        frame = tk.Frame(win, bg=APP_BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=headings[col])
            anchor = "e" if col not in ("date", "item", "party", "status") else "w"
            tree.column(col, width=widths.get(col, 100), anchor=anchor)

        if rows:
            for row in rows:
                tree.insert("", "end", values=row)
        else:
            tree.insert("", "end", values=(empty_message,) + ("",) * (len(columns) - 1))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def show_inventory_report(self):
        rows = []
        for item in db.get_inventory_report():
            rows.append((
                item["item"],
                self._format_qty(item["purchased_qty"]),
                self._format_qty(item["sold_qty"]),
                self._format_qty(item["available_qty"]),
                self._format_money(item["stock_value"]),
                self._format_money(item["sales_value"]),
                self._format_money(item["gross_profit"]),
            ))
        columns = ("item", "purchased", "sold", "available", "stock_value", "sales", "profit")
        headings = {
            "item": "Item", "purchased": "Purchased Qty", "sold": "Sold Qty",
            "available": "Available", "stock_value": "Stock Value",
            "sales": "Sales Value", "profit": "Gross Profit",
        }
        widths = {"item": 190, "purchased": 110, "sold": 100, "available": 100,
                  "stock_value": 120, "sales": 120, "profit": 120}
        self._show_report_window("Inventory Report", columns, headings, widths, rows,
                                 "No item transactions yet")

    def show_low_stock_report(self):
        rows = []
        for item in db.get_low_stock_items(limit=5):
            status = "Out of stock" if item["available_qty"] <= 0 else "Low stock"
            rows.append((
                item["item"],
                self._format_qty(item["available_qty"]),
                self._format_qty(item["sold_qty"]),
                self._format_money(item["stock_value"]),
                status,
            ))
        columns = ("item", "available", "sold", "stock_value", "status")
        headings = {
            "item": "Item", "available": "Available", "sold": "Sold Qty",
            "stock_value": "Stock Value", "status": "Status",
        }
        widths = {"item": 260, "available": 110, "sold": 110, "stock_value": 130, "status": 140}
        self._show_report_window("Low Stock Items", columns, headings, widths, rows,
                                 "No low-stock items")

    def show_party_balances(self):
        rows = []
        for party in db.get_party_balances():
            balance = party["net_balance"] or 0
            status = "Receivable" if balance > 0 else "Payable" if balance < 0 else "Settled"
            rows.append((
                party["party"],
                self._format_money(party["total_credit"]),
                self._format_money(party["total_debit"]),
                self._format_money(balance),
                status,
            ))
        columns = ("party", "credit", "debit", "balance", "status")
        headings = {
            "party": "Party", "credit": "Total Credit", "debit": "Total Debit",
            "balance": "Net Balance", "status": "Status",
        }
        widths = {"party": 260, "credit": 130, "debit": 130, "balance": 130, "status": 120}
        self._show_report_window("Party Balances", columns, headings, widths, rows,
                                 "No parties recorded yet")

    def show_cashbook(self):
        rows = []
        for day in db.get_cashbook(self.date_from.get().strip(), self.date_to.get().strip()):
            rows.append((
                day["date"],
                self._format_money(day["cash_in"]),
                self._format_money(day["cash_out"]),
                self._format_money(day["net"]),
                self._format_money(day["running_balance"]),
            ))
        columns = ("date", "cash_in", "cash_out", "net", "running")
        headings = {
            "date": "Date", "cash_in": "Cash In", "cash_out": "Cash Out",
            "net": "Net Change", "running": "Running Balance",
        }
        widths = {"date": 120, "cash_in": 140, "cash_out": 140, "net": 140, "running": 160}
        self._show_report_window("Daily Cashbook", columns, headings, widths, rows,
                                 "No transactions in this date range")

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])["values"]
        self.selected_id = values[0]
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, values[1])
        self.entry_item.delete(0, "end"); self.entry_item.insert(0, values[2])
        self.entry_party.delete(0, "end"); self.entry_party.insert(0, values[3])
        self.entry_category.set(values[4])
        self.entry_description.delete(0, "end"); self.entry_description.insert(0, values[6])
        self.entry_stock.delete(0, "end"); self.entry_stock.insert(0, values[5])
        self.entry_debit.delete(0, "end"); self.entry_debit.insert(0, values[7])
        self.entry_credit.delete(0, "end"); self.entry_credit.insert(0, values[8])
        row = db.get_transactions()
        selected_row = next((r for r in row if r["id"] == self.selected_id), None)
        if selected_row:
            self.entry_item.delete(0, "end"); self.entry_item.insert(0, selected_row["item"] or "")
            self.entry_buying_rate.delete(0, "end"); self.entry_buying_rate.insert(0, selected_row["buying_rate"] or "")
            self.entry_selling_rate.delete(0, "end"); self.entry_selling_rate.insert(0, selected_row["selling_rate"] or "")
            self.refresh_calculated_amounts()

    def _read_form(self):
        date_val = self.entry_date.get().strip()
        party = self.entry_party.get().strip()
        category = self.entry_category.get().strip() or "Misc Expense"
        description = self.entry_description.get().strip()
        item = self.entry_item.get().strip()
        debit_raw = self.entry_debit.get().strip()
        credit_raw = self.entry_credit.get().strip()
        stock_raw = self.entry_stock.get().strip()
        buying_raw = self.entry_buying_rate.get().strip()
        selling_raw = self.entry_selling_rate.get().strip()
        try:
            debit = float(debit_raw) if debit_raw else 0.0
            credit = float(credit_raw) if credit_raw else 0.0
            stock = float(stock_raw) if stock_raw else 0.0
            buying_rate = float(buying_raw) if buying_raw else 0.0
            selling_rate = float(selling_raw) if selling_raw else 0.0
        except ValueError:
            messagebox.showerror("Invalid input", "Amounts, stock, and rates must be numbers.")
            return None
        if not date_val:
            messagebox.showerror("Invalid input", "Date is required (format: YYYY-MM-DD).")
            return None
        if min(debit, credit, stock, buying_rate, selling_rate) < 0:
            messagebox.showerror("Invalid input", "Amounts, stock, and rates cannot be negative.")
            return None
        return date_val, party, category, description, debit, credit, item, stock, buying_rate, selling_rate

    def refresh_calculated_amounts(self):
        try:
            stock = float(self.entry_stock.get() or 0)
            buying_rate = float(self.entry_buying_rate.get() or 0)
            selling_rate = float(self.entry_selling_rate.get() or 0)
        except ValueError:
            self.calculated_sales_label.config(text="Sales: -- | Purchase: --")
            return
        total_sales = stock * selling_rate
        total_purchase = stock * buying_rate
        self.calculated_sales_label.config(
            text=f"Sales: ₹{total_sales:,.2f} | Purchase: ₹{total_purchase:,.2f}")
        if self.entry_category.get().strip().lower() == "sales":
            self.entry_credit.delete(0, "end"); self.entry_credit.insert(0, f"{total_sales:.2f}")
        elif self.entry_category.get().strip().lower() == "purchases":
            self.entry_debit.delete(0, "end"); self.entry_debit.insert(0, f"{total_purchase:.2f}")

    def add_transaction(self):
        data = self._read_form()
        if not data:
            return
        db.add_transaction(*data)
        db.add_category(data[2])
        self.clear_form()
        self.refresh_table()

    def update_transaction(self):
        if not self.selected_id:
            messagebox.showinfo("No selection", "Select a row in the table first.")
            return
        data = self._read_form()
        if not data:
            return
        db.update_transaction(self.selected_id, *data)
        db.add_category(data[2])
        self.clear_form()
        self.refresh_table()

    def delete_transaction(self):
        if not self.selected_id:
            messagebox.showinfo("No selection", "Select a row in the table first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete the selected transaction?"):
            db.delete_transaction(self.selected_id)
            self.clear_form()
            self.refresh_table()

    def clear_form(self):
        self.selected_id = None
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, date.today().isoformat())
        self.entry_party.delete(0, "end")
        self.entry_category.set("")
        self.entry_description.delete(0, "end")
        self.entry_debit.delete(0, "end")
        self.entry_credit.delete(0, "end")
        self.entry_item.delete(0, "end")
        self.entry_stock.delete(0, "end")
        self.entry_buying_rate.delete(0, "end")
        self.entry_selling_rate.delete(0, "end")
        self.refresh_calculated_amounts()

    # ---------- EXCEL ----------
    def import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Select Excel file to import",
            filetypes=[("Excel files", "*.xlsx *.xlsm")]
        )
        if not filepath:
            return

        header, preview = excel_io.read_excel_preview(filepath)
        mapping = excel_io.detect_columns(header)

        # If date column wasn't auto-detected, ask user to map columns manually
        if mapping.get("date") is None:
            mapping = self._ask_column_mapping(header, preview)
            if mapping is None:
                return

        success, error_count, errors = excel_io.import_excel(filepath, mapping)
        self.refresh_table()

        msg = f"Imported {success} transaction(s) successfully."
        if error_count:
            msg += f"\n{error_count} row(s) had issues and were skipped."
        messagebox.showinfo("Import complete", msg)

    def _ask_column_mapping(self, header, preview):
        """Popup letting the user map Excel columns to ledger fields manually."""
        win = tk.Toplevel(self)
        win.title("Map Excel Columns")
        win.geometry("480x400")
        win.configure(bg="white")

        tk.Label(win, text="We couldn't auto-detect your columns.\nPlease match each field below:",
                 font=FONT_BOLD, bg="white", justify="left").pack(pady=10, padx=10, anchor="w")

        col_options = [f"Column {i+1}: {h}" for i, h in enumerate(header)]
        col_options_with_none = ["(none)"] + col_options
        result = {}
        vars_map = {}

        fields = [("date", "Date *"), ("party", "Party"), ("category", "Category"),
              ("description", "Description"), ("debit", "Debit"), ("credit", "Credit"),
              ("item", "Item"), ("stock", "Stock/Qty"), ("buying_rate", "Buying rate"),
              ("selling_rate", "Selling rate")]

        for field, label in fields:
            row = tk.Frame(win, bg="white")
            row.pack(fill="x", padx=10, pady=4)
            tk.Label(row, text=label, width=14, anchor="w", bg="white", font=FONT_NORMAL).pack(side="left")
            v = tk.StringVar(value="(none)")
            combo = ttk.Combobox(row, values=col_options_with_none, textvariable=v, width=30, state="readonly")
            combo.pack(side="left")
            vars_map[field] = v

        def confirm():
            for field, v in vars_map.items():
                val = v.get()
                if val == "(none)":
                    result[field] = None
                else:
                    idx = col_options.index(val)
                    result[field] = idx
            if result.get("date") is None:
                messagebox.showerror("Missing field", "Date column is required.")
                return
            win.destroy()

        tk.Button(win, text="Confirm mapping", command=confirm, bg=ACCENT, fg="white",
                  font=FONT_BOLD, padx=12, pady=6).pack(pady=16)

        self.wait_window(win)
        return result if result else None

    def export_excel(self):
        filepath = filedialog.asksaveasfilename(
            title="Save ledger as Excel file",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="ledger_export.xlsx"
        )
        if not filepath:
            return
        rows = db.get_transactions()
        excel_io.export_excel(filepath, rows)
        messagebox.showinfo("Export complete", f"Ledger exported to:\n{filepath}")


if __name__ == "__main__":
    app = LedgerApp()
    app.mainloop()
