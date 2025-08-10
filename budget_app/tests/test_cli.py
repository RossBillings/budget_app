"""
Test suite for the Budget App CLI.

These tests verify that all CLI commands work as expected with the SQLite database.
"""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

# Add parent directory to path so we can import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import get_db
from models import Base, Transaction, engine


class TestBudgetAppCLI(unittest.TestCase):
    """Test cases for the Budget App CLI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and data."""
        # Use an in-memory SQLite database for testing
        cls.db_url = "sqlite:///:memory:"
        os.environ["DATABASE_URL"] = cls.db_url
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add some test data
        cls.sample_transactions = [
            {
                "transaction_date": date.today() - timedelta(days=i),
                "description": f"Test Transaction {i}",
                "amount": 10.0 * (i + 1),
                "category": "test",
                "source": "test",
                "dedupe_key": f"test-key-{i}"
            }
            for i in range(5)
        ]
        
        with get_db() as db:
            for txn_data in cls.sample_transactions:
                txn = Transaction(**txn_data)
                db.add(txn)
            db.commit()
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_csv = os.path.join(self.test_dir.name, "test_transactions.csv")
        
        # Create a test CSV file
        with open(self.test_csv, 'w') as f:
            f.write("Transaction Date,Description,Amount,Category\n")
            for i in range(3):
                date_str = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
                f.write(f"{date_str},Test Import {i},{20.0 * (i + 1)},import\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_dir.cleanup()
    
    def test_import_command(self):
        """Test the import command."""
        from __main__ import main
        
        # Test importing a CSV file
        with patch('sys.argv', ['budget_app.py', 'import', self.test_csv, '--category', 'test_import']):
            main()
        
        # Verify the data was imported
        with get_db() as db:
            imported = db.query(Transaction).filter(
                Transaction.category == 'test_import'
            ).all()
            self.assertEqual(len(imported), 3)
    
    def test_report_command(self):
        """Test the report command."""
        from __main__ import main
        
        # Test with no filters
        with patch('sys.argv', ['budget_app.py', 'report', '--category', 'test']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                
                # Check that the output contains expected data
                self.assertIn("Aggregated Expenses by Month", output)
                self.assertIn("Transactions", output)
                self.assertIn("Test Transaction", output)
    
    def test_categories_command(self):
        """Test the categories command."""
        from __main__ import main
        
        with patch('sys.argv', ['budget_app.py', 'categories']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                
                # Check that the output contains the test category
                self.assertIn("test", output)
    
    def test_delete_command(self):
        """Test the delete command."""
        from __main__ import main
        
        # Get a transaction to delete
        with get_db() as db:
            txn = db.query(Transaction).first()
            txn_id = txn.id
        
        # Delete the transaction
        with patch('sys.argv', ['budget_app.py', 'delete', txn_id]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("deleted successfully", output)
        
        # Verify the transaction was deleted
        with get_db() as db:
            txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
            self.assertIsNone(txn)
    
    def test_invalid_import(self):
        """Test error handling for invalid import."""
        from __main__ import main
        
        # Test with non-existent file
        with patch('sys.argv', ['budget_app.py', 'import', 'nonexistent.csv']):
            with self.assertRaises(SystemExit):
                with patch('sys.stderr', new=StringIO()):
                    main()


if __name__ == '__main__':
    unittest.main()
