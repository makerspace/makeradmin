import unittest
import src.db_info as db_info
import src.db_helper as db_helper
import json

class Test(unittest.TestCase):
    def test_UsersColumns(self):
        with open("test/data/Users_columns.json", "r") as f:
            expected_columns = json.load(f)
        actual_columns = db_info.get_column_names(db_helper.create_default_engine(), "Users")
        for c in expected_columns:
            self.assertIn(c, actual_columns, f"Users table should contain the column {c}")

    def test_Tables(self):
        with open("test/data/tables.json", "r") as f:
            expected_tables = json.load(f)
        actual_tables = db_info.get_table_names(db_helper.create_default_engine())
        for c in expected_tables:
            self.assertIn(c, actual_tables, f"Users table should contain the column {c}")