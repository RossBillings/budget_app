# Budget App

The Budget App is a suite of Python scripts designed to help you import, track, and visualize your expenses. It consists of several modules that work together:  
	•	0-budget_app.py: Orchestrates the CSV import, expense tracking, and visualization scripts over a specified date range.  
	•	1-import_csv-TWO.py: Imports and cleans your expense CSV files.  
	•	2-track-expense.py: Processes your expenses, calculates budgets, and generates summary tables and charts.  
	•	3-visualize_budget_history.py: Visualizes your historical budget data.  
	•	gui.py: Provides a graphical interface (Tkinter) with tabs to run both the orchestrator and misc analysis scripts.  

	•	misc_analysis.py: Provides detailed analysis of “Misc” category expenses, including aggregated monthly data, transaction listing, keyword and date-range filtering.

### Features
- CSV Import & Cleanup: Import expense data from CSV files and automatically update your budget categories.  
- Expense Tracking: Summarize expenses by category, compute remaining budgets, and calculate net income.  
- Visualization: Generate attractive charts and tables using PrettyTable and Matplotlib.  
- Miscellaneous Analysis: Focus on the “Misc” category, viewing both aggregated totals by month and detailed transaction listings.  
- Graphical Interface: Launch a Tkinter GUI (`gui.py`) to orchestrate scripts and analyze transactions interactively.

Prerequisites
	•	Python 3.x installed
	•	Required Python packages:
	•	matplotlib
	•	prettytable
	•	tkinter (included with standard Python distribution)

You can install the required packages using:

pip install matplotlib prettytable

## Setup
### 1.	Clone the Repository:

git clone https://github.com/yourusername/budget_app.git
cd budget_app


### 2.	Set Up a Virtual Environment (optional but recommended):

python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate
pip install -r requirements.txt  # If you have a requirements file, or manually install packages


### 3. Prepare Your CSV Files:
	•	Place your expense CSV file (e.g., cleaned_expenses2025.csv) in the Expense_Inputs folder.
	•	Ensure your budget CSV (budgets.csv) is in the same folder. The import script will update this file with any missing categories.

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

## Running the GUI

To launch the graphical interface:

```
python gui.py
```

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