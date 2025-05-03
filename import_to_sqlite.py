#!/usr/bin/env python3
"""
import_to_sqlite.py

Script to load a cleaned expenses CSV into a SQLite database.
"""
import csv
import sqlite3
import argparse
import os


def init_db(db_path, fields):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS expenses;")
    col_defs = []
    for col in fields:
        if col.strip().lower() == 'amount':
            dtype = 'REAL'
        else:
            dtype = 'TEXT'
        col_defs.append(f'"{col}" {dtype}')
    create_sql = f"CREATE TABLE expenses ({', '.join(col_defs)});"
    cursor.execute(create_sql)
    conn.commit()
    return conn


def import_csv_to_db(csv_path, db_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields:
            print("No columns found in CSV.")
            return
        conn = init_db(db_path, fields)
        cursor = conn.cursor()

        placeholders = ', '.join(['?'] * len(fields))
        columns = ', '.join([f'"{col}"' for col in fields])
        insert_sql = f"INSERT INTO expenses ({columns}) VALUES ({placeholders});"

        data = []
        for row in reader:
            vals = []
            for col in fields:
                val = row[col]
                if col.strip().lower() == 'amount':
                    try:
                        val = float(val)
                    except ValueError:
                        val = None
                vals.append(val)
            data.append(vals)

        cursor.executemany(insert_sql, data)
        conn.commit()
        print(f"Imported {len(data)} rows into '{db_path}' (table 'expenses').")
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Import expense CSV into a SQLite DB.")
    parser.add_argument(
        '--csv',
        default=os.path.join('Expense_Inputs', 'cleaned_expenses2025.csv'),
        help='Path to the cleaned expense CSV file.'
    )
    parser.add_argument(
        '--db',
        default='expenses.db',
        help='SQLite database file to create or use.'
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        print(f"CSV file '{args.csv}' not found.")
        return

    import_csv_to_db(args.csv, args.db)


if __name__ == '__main__':
    main()
