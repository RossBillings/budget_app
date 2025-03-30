import os
import subprocess
import argparse
from datetime import datetime, timedelta

def run_script(script_name, args=None):
    """
    Executes a Python script with optional arguments.
    """
    command = ["python", script_name]
    if args:
        command.extend(args)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error while running {script_name}:")
        print(result.stderr)
        return False
    else:
        print(f"Successfully executed {script_name}")
        print(result.stdout)
        return True

def generate_date_range(year_start, month_start, year_end, month_end):
    """
    Generates a list of (year, month) tuples from start to end date.
    """
    start_date = datetime(year_start, month_start, 1)
    end_date = datetime(year_end, month_end, 1)
    current_date = start_date

    date_range = []
    while current_date <= end_date:
        date_range.append((current_date.year, current_date.month))
        # Move to the next month
        next_month = current_date + timedelta(days=31)
        current_date = datetime(next_month.year, next_month.month, 1)

    return date_range

def orchestrate_scripts(year_start, month_start, year_end, month_end):
    """
    Orchestrates the three scripts in sequence and iterates through the date range.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Script paths
    script1 = os.path.join(script_dir, "1-import_csv-TWO.py")
    script2 = os.path.join(script_dir, "2-track-expense.py")
    script3 = os.path.join(script_dir, "3-visualize_budget_history.py")
    
    # Step 1: Run 1-import_csv-TWO.py
    if not run_script(script1):
        return  # Stop the process if script1 fails

    # Step 2: Run 2-track-expense.py for each month in the range
    date_range = generate_date_range(year_start, month_start, year_end, month_end)
    for year, month in date_range:
        print(f"Running {script2} for {year}-{month:02d}")
        if not run_script(script2, [f"--year={year}", f"--month={month}"]):
            return  # Stop the process if script2 fails

    # Step 3: Run 3-visualize_budget_history.py
    if not run_script(script3):
        return  # Stop the process if script3 fails

    print("All scripts executed successfully!")

if __name__ == "__main__":
    # Use argparse to accept all inputs as a single call
    parser = argparse.ArgumentParser(description="Orchestrate the execution of scripts with a given year and month range.")
    parser.add_argument("--start_year", type=int, required=True, help="Starting year")
    parser.add_argument("--start_month", type=int, required=True, help="Starting month (1-12)")
    parser.add_argument("--end_year", type=int, required=True, help="Ending year")
    parser.add_argument("--end_month", type=int, required=True, help="Ending month (1-12)")

    args = parser.parse_args()

    orchestrate_scripts(
        year_start=args.start_year,
        month_start=args.start_month,
        year_end=args.end_year,
        month_end=args.end_month
    )

    # Example Call
    # python 0-budget_app.py --start_year 2024 --start_month 05 --end_year 2024 --end_month 08