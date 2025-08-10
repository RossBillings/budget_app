# Budget App

A powerful, SQLite-based budget tracking and analysis application that helps you manage and visualize your expenses with ease.

The Budget App is a comprehensive Python application designed to help you import, track, and analyze your expenses. It consists of several components:

## Core Components

### Modern CLI Application (`budget_app/`)
- **`__main__.py`**: Main CLI application with commands for importing, reporting, and managing transactions
- **`db.py`**: Database operations and session management with deduplication
- **`models.py`**: SQLAlchemy models with automatic categorization and deduplication
- **`alembic/`**: Database migrations for schema management

### Legacy Scripts
- **`0-budget_app.py`**: Orchestrates the CSV import, expense tracking, and visualization scripts over a specified date range
- **`1-import_csv-TWO.py`**: Imports and cleans your expense CSV files with automatic categorization
- **`2-track-expense.py`**: Processes your expenses, calculates budgets, and generates summary tables and charts
- **`3-visualize_budget_history.py`**: Visualizes your historical budget data
- **`gui.py`**: Provides a graphical interface (Tkinter) with tabs to run both the orchestrator and misc analysis scripts
- **`misc_analysis.py`**: Provides detailed analysis of "Misc" category expenses, including aggregated monthly data, transaction listing, keyword and date-range filtering

### Features
- **SQLite Database**: All your financial data is stored in a single, portable SQLite database file (`budget.db`).
- CSV Import & Cleanup: Import expense data from CSV files and automatically update your budget categories.  
- Expense Tracking: Summarize expenses by category, compute remaining budgets, and calculate net income.  
- Visualization: Generate attractive charts and tables using PrettyTable and Matplotlib.  
- Miscellaneous Analysis: Focus on the “Misc” category, viewing both aggregated totals by month and detailed transaction listings.  
- Graphical Interface: Launch a Tkinter GUI (`gui.py`) to orchestrate scripts and analyze transactions interactively.

## Database Schema

The application uses a single `transactions` table with the following structure:

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

-- Indexes for common query patterns
CREATE INDEX idx_txn_month ON transactions (strftime('%Y-%m', transaction_date));
CREATE INDEX idx_txn_desc_lower ON transactions (lower(description));
CREATE INDEX idx_txn_date_category ON transactions (transaction_date, category);
```

## Prerequisites
	•	Python 3.x installed
	•	Required Python packages:
	•	matplotlib
	•	prettytable
	•	tkinter (included with standard Python distribution)
	•	SQLAlchemy >= 2.0.0
	•	Alembic
	•	python-dateutil

You can install the required packages using:

pip install matplotlib prettytable SQLAlchemy Alembic python-dateutil

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/budget_app.git
   cd budget_app
   ```

2. **Set up a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   # Run Alembic migration to create database schema
   alembic upgrade head
   ```

## Recent Fixes and Improvements

### Database and Import Issues Fixed
- **Fixed deduplication**: Added proper `dedupe_key` generation in CSV import
- **Resolved Alembic hanging**: Fixed database locking issues and migration conflicts
- **Improved error handling**: Added robust error handling for missing files and invalid data
- **Fixed SQLAlchemy session management**: Resolved detached instance errors in queries

### CSV Import Improvements
- **Automatic categorization**: Enhanced keyword-based transaction categorization
- **Duplicate handling**: Improved batch processing to handle duplicates within CSV files
- **Error recovery**: Better error messages and graceful handling of malformed data

### CLI Enhancements
- **Modern interface**: New CLI application with intuitive commands
- **Advanced filtering**: Filter by category, date range, keywords, and sorting options
- **Chart generation**: Export expense charts as PNG files
- **Transaction management**: View, filter, and delete transactions

## Usage

### Modern CLI Application

The main entry point for the modern CLI application is:

```bash
python -m budget_app --help
```

#### Available Commands

**Import Transactions:**
```bash
python -m budget_app import <csv_file>
```

**View Categories:**
```bash
python -m budget_app categories
```

**Generate Reports:**
```bash
# Basic report
python -m budget_app report

# Filter by category
python -m budget_app report --category groceries

# Sort by amount (descending)
python -m budget_app report --category dining --sort-by amount --order desc

# Limit results
python -m budget_app report --limit 10

# Generate chart
python -m budget_app report --category groceries --output chart.png
```

**Delete Transaction:**
```bash
python -m budget_app delete <transaction_id>
```

### Legacy Scripts

**Running the Budget App Orchestrator**

The main entry point for running the whole process is the 0-budget_app.py script. This script orchestrates the execution of all three main modules:
	•	0-budget_app.py:
This script executes the following steps:
	1.	Runs the CSV import/cleanup script (1-import_csv-TWO.py).
	2.	Runs the expense tracker for each month in the specified date range (2-track-expense.py).
	3.	Runs the visualization of budget history (3-visualize_budget_history.py).

To run the orchestrator, use the following command:

```
python 0-budget_app.py --start_year 2025 --start_month 01 --end_year 2025 --end_month 03
```

This command will process expenses from January through March 2025.

Running Miscellaneous Expense Analysis

The misc_analysis.py script focuses on the “Misc” expense category and provides two modes of output:
	•	Aggregated Monthly Analysis: A bar chart and a PrettyTable summarizing Misc expenses per month.
	•	Detailed Transaction List: Optionally, a detailed table of each individual Misc transaction.

Example Commands:
	•	Default Aggregated Analysis:

python misc_analysis.py


	•	Sort Aggregated Data by Value (Descending Order):

python misc_analysis.py --sort_by value --order desc


	•	List Individual Misc Transactions:

python misc_analysis.py --list_transactions --sort_by date --order asc


	•	Save the Chart to a File Instead of Displaying:

python misc_analysis.py --output misc_chart.png

## Development

### Project Structure

```
budget_app/
├── budget_app/                    # Main package
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy models with deduplication
│   │   └── database.py           # Database operations and session management
│   ├── cli/                      # CLI commands
│   │   ├── __init__.py
│   │   └── commands.py           # CLI command implementations
│   ├── legacy/                   # Legacy scripts (backward compatibility)
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # 0-budget_app.py
│   │   ├── csv_import.py         # 1-import_csv-TWO.py
│   │   ├── expense_tracker.py    # 2-track-expense.py
│   │   ├── visualizer.py         # 3-visualize_budget_history.py
│   │   ├── gui.py                # GUI interface
│   │   ├── misc_analysis.py      # Misc analysis
│   │   ├── budget_adv.py         # Budget helper
│   │   ├── expense_adv.py        # Expense helper
│   │   ├── category_loader.py    # Category helper
│   │   └── budget_analysis_writer.py # Analysis writer
│   ├── tests/                    # Unit tests
│   └── alembic/                  # Database migrations
├── scripts/                      # Standalone utility scripts
│   ├── 1.5-expense_trends.py
│   └── 4-deep_keyword_analysis.py
├── data/                         # Data files
│   ├── inputs/                   # Input CSV files
│   └── outputs/                  # Generated charts/reports
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── alembic.ini                   # Alembic configuration
├── budget.db                     # SQLite database (created automatically)
└── README.md                     # This file
```

### Adding New Features

1. Create a new branch for your feature
2. Add tests for the new functionality
3. Implement the feature
4. Run tests and ensure they pass
5. Create a pull request

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Use the GUI tabs to run the orchestrator (0-budget_app) and misc analysis scripts interactively.

Additional Information
	•	CSV Formats:
Make sure your CSV files use the proper headers (e.g., Transaction Date, Description, Amount, Category).
	•	Handling Transfers:
The import script ignores rows with descriptions like “USAA Transfer” to prevent double counting when transferring funds between accounts.
	•	Sign Corrections:
The script adjusts the sign of amounts for specific inputs (like USAA) so that your expenses and incomes are correctly represented.

Contributing

If you have ideas or improvements, feel free to open an issue or submit a pull request.

## Troubleshooting

### Common Issues

**Alembic Migration Hangs:**
```bash
# Kill any running Python processes
pkill -f python

# Remove WAL files to reset database state
rm -f budget.db-shm budget.db-wal

# Run migration again
alembic upgrade head
```

**Import Errors:**
- Ensure CSV files have proper headers: `Transaction Date`, `Description`, `Amount`, `Category`
- Check file permissions and paths
- Verify CSV encoding (UTF-8 recommended)

**Database Lock Issues:**
- Close any other applications using the database
- Restart the application
- If persistent, delete and recreate the database: `rm budget.db && alembic upgrade head`

### CSV Format Requirements

The application supports two CSV formats:

1. **Capital One Format**: Columns include `Transaction Date`, `Description`, `Debit`, `Credit`
2. **USAA Format**: Columns include `Date`, `Description`, `Amount`

The import process automatically detects the format and handles sign corrections appropriately.

## License

This project is open-sourced under the MIT License.