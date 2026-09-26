"""Tests for category-by-month summary."""
import importlib
import os
import tempfile
import unittest
from datetime import date
from io import StringIO
from unittest.mock import patch

from budget_app.cli.commands import (
    _month_money_flow,
    print_category_monthly_table,
    resolve_summary_date_range,
)


class TestResolveSummaryDateRange(unittest.TestCase):
    def _args(self, **kwargs):
        return argparse_namespace(**kwargs)

    def test_single_month(self):
        ns = self._args(month='2026-01')
        start, end = resolve_summary_date_range(ns)
        self.assertEqual(start, '2026-01-01')
        self.assertEqual(end, '2026-01-31')

    def test_month_range(self):
        ns = self._args(start_month='2025-11', end_month='2026-02')
        start, end = resolve_summary_date_range(ns)
        self.assertEqual(start, '2025-11-01')
        self.assertEqual(end, '2026-02-28')

    def test_multiple_years(self):
        ns = self._args(year=[2024, 2026])
        start, end = resolve_summary_date_range(ns)
        self.assertEqual(start, '2024-01-01')
        self.assertEqual(end, '2026-12-31')

    def test_conflicting_filters(self):
        ns = self._args(month='2026-01', year=[2026])
        with self.assertRaises(ValueError):
            resolve_summary_date_range(ns)


class TestCategoryMonthlyTotals(unittest.TestCase):
    def setUp(self):
        self.db_path = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_path}'

        import budget_app.core.models as models
        import budget_app.core.database as database

        importlib.reload(models)
        importlib.reload(database)

        models.Base.metadata.create_all(bind=models.engine)
        self.database = database
        self.Transaction = models.Transaction

        with database.get_db() as db:
            db.add_all([
                self.Transaction(
                    transaction_date=date(2026, 1, 5),
                    description='Store A',
                    amount=100.0,
                    category='groceries',
                    source='test',
                    dedupe_key='k1',
                ),
                self.Transaction(
                    transaction_date=date(2026, 1, 20),
                    description='Store B',
                    amount=50.0,
                    category='groceries',
                    source='test',
                    dedupe_key='k2',
                ),
                self.Transaction(
                    transaction_date=date(2026, 2, 1),
                    description='Cafe',
                    amount=30.0,
                    category='dining',
                    source='test',
                    dedupe_key='k3',
                ),
                self.Transaction(
                    transaction_date=date(2026, 2, 10),
                    description='USAA Transfer',
                    amount=500.0,
                    category='transfer',
                    source='test',
                    dedupe_key='k4',
                ),
                self.Transaction(
                    transaction_date=date(2026, 2, 15),
                    description='Paycheck',
                    amount=-1000.0,
                    category='income',
                    source='test',
                    dedupe_key='k5',
                ),
            ])
            db.commit()

    def test_totals_grouped_by_month_and_category(self):
        rows = self.database.get_category_monthly_totals()
        categories = {r['category'] for r in rows}
        self.assertNotIn('transfer', categories)
        self.assertEqual(len(rows), 3)
        groceries_jan = next(
            r for r in rows if r['month'] == '2026-01' and r['category'] == 'groceries'
        )
        self.assertEqual(groceries_jan['total'], 150.0)

    def test_explicit_transfer_category_not_excluded(self):
        rows = self.database.get_category_monthly_totals(category='transfer')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['total'], 500.0)

    def test_month_money_flow(self):
        rows = self.database.get_category_monthly_totals(
            start_date='2026-02-01',
            end_date='2026-02-28',
        )
        money_in, money_out, net = _month_money_flow(rows)
        self.assertEqual(money_in, 1000.0)
        self.assertEqual(money_out, 30.0)
        self.assertEqual(net, 970.0)

    def test_filter_single_month(self):
        rows = self.database.get_category_monthly_totals(
            start_date='2026-02-01',
            end_date='2026-02-28',
        )
        self.assertEqual(len(rows), 2)
        by_cat = {r['category']: r['total'] for r in rows}
        self.assertEqual(by_cat['dining'], 30.0)
        self.assertEqual(by_cat['income'], -1000.0)


class TestPrintCategoryMonthlyTable(unittest.TestCase):
    def test_table_per_month(self):
        rows = [
            {'month': '2026-01', 'category': 'income', 'total': -200.0},
            {'month': '2026-01', 'category': 'groceries', 'total': 100.0},
            {'month': '2026-01', 'category': 'dining', 'total': 50.0},
            {'month': '2026-02', 'category': 'groceries', 'total': 30.0},
        ]
        with patch('sys.stdout', new=StringIO()) as out:
            print_category_monthly_table(rows, pivot=False)
            text = out.getvalue()

        self.assertIn('2026-01', text)
        self.assertIn('2026-02', text)
        self.assertNotIn('|  transfer ', text)
        self.assertIn('Money in', text)
        self.assertIn('Money out', text)
        self.assertIn('Net', text)
        self.assertIn('$200.00', text)


def argparse_namespace(**kwargs):
    class NS:
        pass

    ns = NS()
    ns.month = kwargs.get('month')
    ns.start_month = kwargs.get('start_month')
    ns.end_month = kwargs.get('end_month')
    ns.year = kwargs.get('year')
    ns.start_date = kwargs.get('start_date')
    ns.end_date = kwargs.get('end_date')
    return ns


if __name__ == '__main__':
    unittest.main()
