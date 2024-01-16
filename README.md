# budget_app
    Goals: User enters expense, upload CSV
    ave to CSV
    Summarize expense totals
    Show remaining budget
    Expense Tracker Script
#  Overview
This script is designed to help track and analyze personal expenses. It reads expense data from a CSV file, categorizes expenses, and provides a summary including comparisons with budgeted amounts.

# Features
Summarize expenses by category for a specific month.
Compare actual spending against budgeted amounts.
Generate a bar chart visualizing the budget versus actual spending.
Optional command-line interface for filtering expenses by category.
Setup
Ensure Python 3 is installed on your system.
Install required Python packages, if not already installed:

```python3 -m venv venv```
``` source venv/bin/activate```
``` pip install matplotlib ```

Clone the repository or download the script files to your local machine.

# Usage
Standard Usage
Run the script normally, and it will prompt for the year and month to analyze:

``` python3 track-expense.py ```

Command-Line Interface
To filter expenses by a specific category for a given year and month, use the command-line arguments:

``` python3 track-expense.py --category <category_name> --year <year> --month <month> ```

For example, to view expenses for 'Groceries' in December 2023:

css
``` python3 track-expense.py --category Groceries --year 2023 --month 12 ``

EXAMPLE
``` python3 track-expense.py --category Groceries --year 2023 --month 12 ``

Input File Format
The script expects a CSV file named cleaned_expenses.csv with the following columns:

Transaction Date (format: YYYY-MM-DD)
Description
Category
Amount
Ensure this file is placed in the correct directory or update the script with the appropriate file path.

Output
The script outputs the following:

A text summary of expenses categorized by budget categories.
A bar chart showing the comparison between budgeted and actual expenses (displayed or saved as an image file).
Notes
Modify budgets.csv to reflect your personal budget categories and amounts.
The script assumes a specific structure for the input CSV file. Ensure the format matches the expected structure.