# Budget App
A tool designed to help users track and analyze personal expenses. It allows users to enter expenses, upload CSV data, and visualize financial activity against their budget.

## Goals
- Allow users to input expenses manually or via CSV upload.
- Save expenses to a CSV file for record-keeping.
- Summarize expenses by category for a specified period.
- Compare actual spending against budgeted amounts and visualize the data.

## Overview
This script provides a comprehensive analysis of personal expenses. It categorizes expenses from a CSV file and compares them against budgeted amounts, providing a visual summary that includes budget vs. actual spending.

## Features
- Summarize expenses by category for a specific month and year.
- Compare actual spending against budgeted amounts.
- Generate bar charts visualizing the budget vs. actual spending by category across months.
- Optional command-line interface for filtering expenses by category and visualizing spending history.

## Setup
1. Ensure Python 3 and pip are installed on your system.
2. Set up a virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install matplotlib

Clone the repository or download the script files to your local machine.

# Usage
Run the script normally, and it will prompt for the year and month to analyze:

``` python3 track-expense.py ```

# Command-Line Interface
To filter expenses by a specific category for a given year and month, use the command-line arguments:

``` python3 track-expense.py --category <category_name> --year <year> --month <month> ```

For example, to view expenses for 'Groceries' in December 2023:

css
``` python3 track-expense.py --category Groceries --year 2023 --month 12 ``

EXAMPLE
``` python3 track-expense.py --category Groceries --year 2023 --month 12 ``


# Visualizing Budget History
To visualize spending for each category over different months, run the visualization script:

``` python3 visualize_budget_history.py ```

This will generate bar charts for each category, showing spending over the months, and save them to the Output directory.

# Input File Format
The script expects a CSV file named cleaned_expenses.csv with the following columns:

Transaction Date (format: YYYY-MM-DD)
Description
Category
Amount
Ensure this file is placed in the correct directory or update the script with the appropriate file path.

# Output
The script provides the following outputs:

A text summary of expenses categorized by budget categories.
Bar charts comparing budgeted and actual expenses, saved as image files.
Visuals for historical budget analysis, showing spending trends over time.

# Notes
Modify budgets.csv to reflect your personal budget categories and amounts.



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

