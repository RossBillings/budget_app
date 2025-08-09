# Budget App

A powerful, SQLite-based budget tracking and analysis application that helps you manage and visualize your expenses with ease.

The Budget App is a suite of Python scripts designed to help you import, track, and visualize your expenses. It consists of several modules that work together:  
	•	0-budget_app.py: Orchestrates the CSV import, expense tracking, and visualization scripts over a specified date range.  
	•	1-import_csv-TWO.py: Imports and cleans your expense CSV files.  
	•	2-track-expense.py: Processes your expenses, calculates budgets, and generates summary tables and charts.  
	•	3-visualize_budget_history.py: Visualizes your historical budget data.  
	•	gui.py: Provides a graphical interface (Tkinter) with tabs to run both the orchestrator and misc analysis scripts.  

	•	misc_analysis.py: Provides detailed analysis of “Misc” category expenses, including aggregated monthly data, transaction listing, keyword and date-range filtering.

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
   The database will be created automatically when you run the application for the first time.

## Usage

Running the Budget App Orchestrator

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

- `budget_app/`
  - `__main__.py` - Main CLI application
  - `db.py` - Database operations and session management
  - `models.py` - SQLAlchemy models
  - `alembic/` - Database migrations
  - `tests/` - Unit tests

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

License

This project is open-sourced under the MIT License.

⸻

This README provides an overview of the repository, installation and setup instructions, usage examples for both the orchestrator and the miscellaneous analysis script, and additional context about CSV formats and handling transfers. Adjust the details as needed to match your exact repository structure and project requirements.