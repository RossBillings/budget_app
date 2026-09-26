"""Tests that re-importing a CSV skips existing rows instead of failing."""
import importlib
import os
import tempfile
import unittest


class TestImportDeduplication(unittest.TestCase):
  def setUp(self):
    self.db_path = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

    import budget_app.core.models as models
    import budget_app.core.database as database

    importlib.reload(models)
    importlib.reload(database)

    models.Base.metadata.create_all(bind=models.engine)
    self.import_csv = database.import_transactions_from_csv

    self.csv_path = tempfile.mktemp(suffix=".csv")
    with open(self.csv_path, "w") as f:
      f.write("Transaction Date,Description,Amount,Category\n")
      f.write("2026-05-01,Test Store,42.50,Groceries\n")

  def test_reimport_skips_duplicates(self):
    first = self.import_csv(self.csv_path)
    second = self.import_csv(self.csv_path)

    self.assertEqual(first["inserted"], 1)
    self.assertEqual(first["errors"], 0)
    self.assertEqual(second["inserted"], 0)
    self.assertEqual(second["duplicates"], 1)
    self.assertEqual(second["errors"], 0)


if __name__ == "__main__":
  unittest.main()
