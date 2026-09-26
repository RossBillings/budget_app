"""Tests for multi-format CSV import parsing."""
import unittest

from budget_app.core.categorizer import load_category_rules
from budget_app.core.models import Transaction


class TestCsvRowParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_category_rules()

    def test_standard_format(self):
        row = {
            "Transaction Date": "2026-05-01",
            "Description": "Test Store",
            "Amount": "42.50",
            "Category": "Groceries",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules)
        self.assertEqual(txn.transaction_date.isoformat(), "2026-05-01")
        self.assertEqual(txn.amount, 42.50)
        self.assertEqual(txn.bank_category, "groceries")

    def test_capone_maps_to_groceries(self):
        row = {
            "Transaction Date": "2026-05-12",
            "Posted Date": "2026-05-13",
            "Card No.": "2830",
            "Description": "WEGMANS OWINGS MILLS #125",
            "Category": "Merchandise",
            "Debit": "315.29",
            "Credit": "",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules)
        self.assertEqual(txn.category, "groceries")
        self.assertEqual(txn.bank_category, "merchandise")

    def test_capone_debit_dining_keyword(self):
        row = {
            "Transaction Date": "2026-05-10",
            "Posted Date": "2026-05-11",
            "Card No.": "6161",
            "Description": "CHIPOTLE 1234",
            "Category": "Dining",
            "Debit": "62.50",
            "Credit": "",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules)
        self.assertEqual(txn.amount, 62.50)
        self.assertEqual(txn.category, "dining")

    def test_capone_credit_excluded(self):
        row = {
            "Transaction Date": "2026-05-15",
            "Posted Date": "2026-05-16",
            "Card No.": "6161",
            "Description": "CAPITAL ONE MOBILE PYMT",
            "Category": "Payment/Credit",
            "Debit": "",
            "Credit": "4646.38",
        }
        with self.assertRaises(ValueError):
            Transaction.from_csv_row(row, rules=self.rules)

    def test_usaa_expense(self):
        row = {
            "Date": "2026-05-14",
            "Description": "Chase Credit Card",
            "Original Description": "CHASE CREDIT CRD AUTOPAY",
            "Category": "Credit Card Payment",
            "Amount": "-93.19",
            "Status": "Posted",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules)
        self.assertEqual(txn.amount, 93.19)
        self.assertEqual(txn.category, "bilbrowhomes")

    def test_usaa_income(self):
        row = {
            "Date": "2026-05-15",
            "Description": "Istari Federal Payroll",
            "Original Description": "Istari Federal PAYROLL",
            "Category": "Paycheck",
            "Amount": "6528.17",
            "Status": "Posted",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules)
        self.assertEqual(txn.amount, -6528.17)
        self.assertEqual(txn.category, "income")

    def test_usaa_tithe_from_description(self):
        row = {
            "Date": "2026-04-15",
            "Description": "Horizon Church",
            "Original Description": "",
            "Category": "",
            "Amount": "-1020.00",
            "Status": "Scheduled Bill Pay",
        }
        txn = Transaction.from_csv_row(row, rules=self.rules, default_category="misc")
        self.assertEqual(txn.category, "tithe")

    def test_zero_amount_raises(self):
        row = {
            "Transaction Date": "2026-02-21",
            "Description": "SANTONI'S MARKET",
            "Amount": "0",
            "Category": "Merchandise",
        }
        with self.assertRaises(ValueError):
            Transaction.from_csv_row(row, rules=self.rules)


if __name__ == "__main__":
    unittest.main()
