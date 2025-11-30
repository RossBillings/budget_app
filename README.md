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
- **Smart Duplicate Detection**: Each transaction is checked individually for duplicates before insertion, preventing data duplication across multiple imports.
- **Configurable Categorization**: YAML-based category configuration system - easily modify categorization rules without changing code.
- **Multi-Format CSV Import**: Automatically detects and imports Capital One, USAA, and Chase United CSV formats with appropriate category mapping.
- **Expense Tracking**: Summarize expenses by category, compute remaining budgets, and calculate net income.  
- **Visualization**: Generate attractive charts and tables using PrettyTable and Matplotlib.  
- **Advanced Analysis**: Focus on specific categories or keywords, with detailed transaction filtering and trend analysis.
- **Modern CLI Interface**: Intuitive command-line tools for importing, reporting, and managing financial data.
- **Graphical Interface**: Launch a Tkinter GUI (`gui.py`) to orchestrate scripts and analyze transactions interactively.

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
- **Enhanced duplicate detection**: Individual transaction checking with immediate feedback (default mode)
- **Configurable categorization**: YAML-based category rules - no more hardcoded keywords!
- **Multi-format support**: Auto-detection of Capital One, USAA, and Chase United CSV formats
- **Flexible processing modes**: Choose between individual checking (precise) or batch processing (fast)
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
# Import any supported CSV format (auto-detected with individual duplicate checking)
python -m budget_app import <csv_file>

# Import with specific source identifier
python -m budget_app import <csv_file> --source chase_united

# Use batch processing for large files (faster but less detailed feedback)
python -m budget_app import <csv_file> --batch-mode --batch-size 1000

# Examples
python -m budget_app import data/inputs/Expense_Inputs/capone_transactions.csv
python -m budget_app import data/inputs/Expense_Inputs/usaa_transactions.csv
python -m budget_app import data/inputs/Expense_Inputs/Chaseunited_Activity20231124_20251124_20251125.CSV --source chase_united

# Large file import with batch processing
python -m budget_app import large_file.csv --batch-mode
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
├── scripts/                      # Standalone utility scripts (see scripts/README.md)
│   ├── 1.5-expense_trends.py        # Analyze misc transactions for recategorization
│   ├── 4-deep_keyword_analysis.py   # Find transactions by keyword, export to CSV
│   ├── category_manager.py          # Comprehensive category analysis and updates
│   ├── update_categories.py         # Quick manual transaction updates
│   ├── manage_categories_config.py  # Manage YAML configuration file
│   ├── recategorize_all_transactions.py  # Full database recategorization
│   ├── apply_safe_recategorizations.py   # Apply safe improvements only
│   ├── quick_category_commands.py   # Power user Python functions
│   └── README.md                    # Complete scripts documentation
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

The application supports three CSV formats:

1. **Capital One Format**: Columns include `Transaction Date`, `Description`, `Debit`, `Credit`
2. **USAA Format**: Columns include `Date`, `Description`, `Amount`
3. **Chase United Format**: Columns include `Transaction Date`, `Post Date`, `Description`, `Category`, `Type`, `Amount`, `Memo`

The import process automatically detects the format and handles sign corrections appropriately.

#### Transaction Sign Handling

**All transaction amounts are normalized during import to ensure consistency:**

- **Normal expenses** → **Positive amounts** (e.g., groceries: `+$50.00`)
- **Refunds/returns** → **Negative amounts** (e.g., store return: `-$25.00`) 
- **Income/credits** → **Negative amounts** (since they reduce net spending)

This normalization happens regardless of the original CSV format:
- **Capital One**: Debits (expenses) become positive, credits become negative
- **Chase United**: Sales (expenses) become positive, returns become negative
- **USAA**: Negative amounts become positive for expenses

**Example transformation:**
```
Before: WEGMANS OWINGS MILLS #125 | $-303.56 (negative in CSV)
After:  WEGMANS OWINGS MILLS #125 | $303.56  (positive expense)
```

#### Chase United Format Details

The Chase United format includes pre-categorized transactions that are automatically mapped to your budget categories:

- **Shopping** → target
- **Groceries** → groceries  
- **Food & Drink** → dining
- **Gas** → gas
- **Home** → home_supplies
- **Travel** → automotive
- **Entertainment** → misc
- **Health & Wellness** → health
- **Personal** → misc
- **Gifts & Donations** → tithe
- **Bills & Utilities** → utilities
- **Transfer/Payment** → transfer

The date format supports both MM/DD/YYYY (Chase format) and YYYY-MM-DD formats.

## Category Configuration System

The application uses a flexible YAML-based configuration system for transaction categorization, eliminating hardcoded rules and making it easy to customize categorization logic.

### Configuration File: `config/categories.yaml`

The main configuration file contains:

- **Category Keywords**: Lists of keywords that trigger specific categories
- **External Mappings**: How external categories (Chase, etc.) map to internal categories  
- **Priority Rules**: Order in which categories are checked
- **Settings**: Default category, case sensitivity, etc.

### Managing Category Configuration

```bash
# View all categories and keywords
python scripts/manage_categories_config.py list

# View external category mappings  
python scripts/manage_categories_config.py mappings

# Add a new keyword to a category
python scripts/manage_categories_config.py add --category utilities --keyword "comcast"

# Remove a keyword from a category
python scripts/manage_categories_config.py remove --category misc --keyword "old_keyword" 

# Test categorization on a description
python scripts/manage_categories_config.py test --description "NETFLIX MONTHLY"

# Search for existing keywords
python scripts/manage_categories_config.py search --search-term "target"

# Interactive management mode
python scripts/manage_categories_config.py interactive
```

### Configuration Benefits

- **No Code Changes**: Modify categorization rules by editing YAML file
- **Easy Maintenance**: Add/remove keywords without touching source code
- **Consistent Logic**: All categorization uses the same rule engine
- **Version Control**: Configuration changes are tracked in git
- **Flexible Mappings**: Support for different external CSV formats

## Scripts and Tools

The `scripts/` folder contains powerful analysis and management tools. See **[scripts/README.md](scripts/README.md)** for complete documentation.

### Quick Reference

```bash
# Analyze misc transactions for recategorization
python scripts/1.5-expense_trends.py

# Find all transactions containing a keyword  
python scripts/4-deep_keyword_analysis.py "TARGET"

# Comprehensive category management
python scripts/category_manager.py interactive

# Recategorize all transactions with new config
python scripts/recategorize_all_transactions.py analyze

# Apply safe improvements only
python scripts/apply_safe_recategorizations.py

# Manage configuration file
python scripts/manage_categories_config.py interactive
```

## License

This project is open-sourced under the MIT License.