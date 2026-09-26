# Budget App

A SQLite-based budget tracking and analysis application. Import bank CSVs, categorize transactions, and view spending by category and month.

## Prerequisites

- Python 3.x
- See `requirements.txt` for packages (SQLAlchemy, Alembic, matplotlib, prettytable, PyYAML, python-dateutil)

## Installation

```bash
git clone https://github.com/yourusername/budget_app.git
cd budget_app
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

## Usage

Entry point:

```bash
python -m budget_app --help
```

### Import transactions

```bash
python -m budget_app import Inputs/CAPOne_01-0515_2026.csv
python -m budget_app import Inputs/USAA_01-0515_2026.csv
```

Import applies rules from `categories.yaml`. After editing that file:

```bash
python -m budget_app recategorize
python -m budget_app recategorize --config /path/to/categories.yaml
```

Keywords match substrings in the description (case-insensitive; punctuation ignored). For unnamed checks, use a stable part of the check number (e.g. `check 9955` for recurring tithe checks #995518, #995519, …).

### Category totals by month (`summary`)

Shows spending **by category and month** from `budget.db`.

```bash
# All data (one table per month: Category | Total)
python -m budget_app summary

# Single month
python -m budget_app summary --month 2026-01

# Range of months
python -m budget_app summary --start-month 2025-06 --end-month 2026-02

# One or more calendar years
python -m budget_app summary --year 2026
python -m budget_app summary --year 2024 --year 2025

# Arbitrary date range
python -m budget_app summary --start-date 2026-01-01 --end-date 2026-03-31

# One category only
python -m budget_app summary --year 2026 --category groceries

# Pivot: categories as rows, months as columns
python -m budget_app summary --year 2026 --pivot
```

Use only one filter group: `--month`, `--start-month`/`--end-month`, `--year`, or `--start-date`/`--end-date`.

Transfers are excluded from summaries (internal account moves). Each month ends with **Money in**, **Money out**, and **Net** (income is shown as positive; spending sums positive expense categories).

### Reports (`report`)

Per-category monthly totals, transaction list, and optional chart.

```bash
python -m budget_app report
python -m budget_app report --category groceries
python -m budget_app report --category groceries --output groceries.png
python -m budget_app report --category misc --output misc.png
python -m budget_app report --category dining --sort-by amount --order desc --limit 10
```

**Full month (transactions + chart):**

```bash
# One month, all categories
python -m budget_app report --start-date 2026-01-01 --end-date 2026-01-31

# One month, one category
python -m budget_app report --category groceries --start-date 2026-01-01 --end-date 2026-01-31

# Full year (do not combine with --start-date / --end-date)
python -m budget_app report --year 2026
```

`report` aggregates **by month** (one total per month). For **category × month**, use `summary` above. `categories` lists all-time totals per category only.

### Other commands

```bash
python -m budget_app categories
python -m budget_app delete <transaction_id>
```

### Legacy: budget vs spent

Reads CSVs under `budget_app/legacy/Expense_Inputs/` (not `budget.db`):

```bash
python -m budget_app.legacy.expense_tracker --year 2026 --month 1

python -m budget_app.legacy.orchestrator \
  --start_year 2026 --start_month 1 --end_year 2026 --end_month 12
```

Orchestrator builds `budget_app/legacy/Output/budget_history.csv` (Year, Month, Category, Budgeted, Spent, Remaining). Visualize with:

```bash
python -m budget_app.legacy.visualizer
```

### Legacy: misc analysis

```bash
python -m budget_app.legacy.misc_analysis
python -m budget_app.legacy.misc_analysis --sort_by value --order desc
python -m budget_app.legacy.misc_analysis --list_transactions --sort_by date --order asc
python -m budget_app.legacy.misc_analysis --output misc_chart.png
```

Use the Tkinter GUI (`budget_app/legacy/gui.py`) to run the orchestrator and misc analysis interactively.

## Troubleshooting

**Alembic migration hangs:**

```bash
pkill -f python
rm -f budget.db-shm budget.db-wal
alembic upgrade head
```

**Import errors:** CSV headers must match Capital One (`Transaction Date`, `Description`, `Debit`, `Credit`) or USAA (`Date`, `Description`, `Amount`). Use UTF-8.

**Database lock:** Close other apps using `budget.db`. If needed: `rm budget.db && alembic upgrade head` (destroys data).

**Transfers:** Import skips rows like “USAA Transfer” to avoid double counting.

## Architecture

### Modern CLI (`budget_app/`)

| Module | Role |
|--------|------|
| `__main__.py` | CLI entry point |
| `cli/commands.py` | Commands: import, report, summary, categories, recategorize, delete |
| `core/models.py` | SQLAlchemy models, dedupe keys |
| `core/database.py` | CRUD, import, aggregations |
| `core/categorizer.py` | `categories.yaml` rules |
| `alembic/` | Schema migrations |

### Legacy scripts (`budget_app/legacy/`)

- `orchestrator.py` — import + monthly expense tracker + history CSV
- `csv_import.py`, `expense_tracker.py`, `visualizer.py`
- `misc_analysis.py`, `gui.py`

### Database schema

```sql
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'csv',
    dedupe_key TEXT UNIQUE NOT NULL
);

CREATE INDEX idx_txn_month ON transactions (strftime('%Y-%m', transaction_date));
CREATE INDEX idx_txn_desc_lower ON transactions (lower(description));
CREATE INDEX idx_txn_date_category ON transactions (transaction_date, category);
```

### Project structure

```
budget_app/
├── budget_app/
│   ├── __main__.py
│   ├── cli/commands.py
│   ├── core/
│   │   ├── models.py
│   │   ├── database.py
│   │   └── categorizer.py
│   ├── legacy/
│   ├── tests/
│   └── alembic/
├── scripts/
├── Inputs/              # Bank CSV exports
├── categories.yaml
├── budget.db
├── requirements.txt
└── README.md
```

### Development

1. Branch, implement, add tests, run tests, open a PR.

```bash
python -m pytest budget_app/tests/ -q
```

Contributions welcome via issues and pull requests.

## License

MIT — see [LICENSE](LICENSE).
