#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess, threading, sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class BudgetAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Budget App GUI")
        self.geometry("900x700")
        self.create_widgets()

    def create_widgets(self):
        nb = ttk.Notebook(self)
        tab1 = ttk.Frame(nb)
        tab2 = ttk.Frame(nb)
        nb.add(tab1, text="Orchestrator")
        nb.add(tab2, text="Misc Analysis")
        nb.pack(expand=1, fill='both')

        # Orchestrator tab inputs
        orch_fields = [("Start Year", "start_year"),
                       ("Start Month", "start_month"),
                       ("End Year",   "end_year"),
                       ("End Month",  "end_month")]
        self.orch_vars = {}
        for i, (label, var) in enumerate(orch_fields):
            ttk.Label(tab1, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            ent = ttk.Entry(tab1)
            ent.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            self.orch_vars[var] = ent
        ttk.Button(tab1, text="Run Budget Orchestrator", command=self.run_orchestrator).grid(row=len(orch_fields), column=0, columnspan=2, pady=10)

        # Analysis tab inputs
        ttk.Label(tab2, text="Input CSV").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.analysis_input = ttk.Entry(tab2, width=50)
        self.analysis_input.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Button(tab2, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)

        ana_fields = [("Category", "category"), ("Keyword", "keyword"),
                      ("Start Date (YYYY-MM-DD)", "start_date"),
                      ("End Date (YYYY-MM-DD)",   "end_date")]
        self.ana_vars = {}
        for i, (label, var) in enumerate(ana_fields, start=1):
            ttk.Label(tab2, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            ent = ttk.Entry(tab2)
            ent.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            self.ana_vars[var] = ent
        ttk.Label(tab2, text="Sort By").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.sort_by_cb = ttk.Combobox(tab2, values=["date", "value"], state="readonly", width=10)
        self.sort_by_cb.current(0)
        self.sort_by_cb.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(tab2, text="Order").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        self.order_cb = ttk.Combobox(tab2, values=["asc", "desc"], state="readonly", width=10)
        self.order_cb.current(0)
        self.order_cb.grid(row=6, column=1, padx=5, pady=5, sticky='w')

        ttk.Button(tab2, text="Run Misc Analysis", command=self.run_analysis).grid(row=7, column=0, columnspan=3, pady=10)

        # Output console
        self.output = scrolledtext.ScrolledText(self)
        self.output.pack(expand=1, fill='both', padx=5, pady=5)

    def browse_file(self):
        path = filedialog.askopenfilename(initialdir=SCRIPT_DIR, filetypes=[("CSV Files","*.csv"),("All Files","*.*")])
        if path:
            self.analysis_input.delete(0, tk.END)
            self.analysis_input.insert(0, path)

    def execute_command(self, cmd):
        self.output.delete(1.0, tk.END)
        try:
            p = subprocess.Popen(cmd, cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                self.output.insert(tk.END, line)
                self.output.see(tk.END)
            p.wait()
        except Exception as e:
            self.output.insert(tk.END, str(e))

    def run_orchestrator(self):
        args = []
        for var in ["start_year","start_month","end_year","end_month"]:
            val = self.orch_vars[var].get().strip()
            if not val:
                self.output.insert(tk.END, f"Please fill {var}.\n")
                return
            args.extend([f"--{var}", val])
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "0-budget_app.py")] + args
        threading.Thread(target=self.execute_command, args=(cmd,)).start()

    def run_analysis(self):
        input_file = self.analysis_input.get().strip() or os.path.join(SCRIPT_DIR, "Expense_Inputs","cleaned_expenses2025.csv")
        args = ["--input", input_file,
                "--category", self.ana_vars["category"].get().strip(),
                "--keyword",  self.ana_vars["keyword"].get().strip(),
                "--start_date", self.ana_vars["start_date"].get().strip(),
                "--end_date",   self.ana_vars["end_date"].get().strip(),
                "--sort_by",   self.sort_by_cb.get(),
                "--order",     self.order_cb.get()]
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "misc_analysis.py")] + args
        threading.Thread(target=self.execute_command, args=(cmd,)).start()

if __name__ == "__main__":
    app = BudgetAppGUI()
    app.mainloop()
