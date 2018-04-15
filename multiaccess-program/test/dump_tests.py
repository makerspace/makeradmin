import unittest
import src.dump as dump
import src.db_helper as db_helper

class Test(unittest.TestCase):
    def setUp(self):
        self.db = db_helper.create_default_engine()

    def test_table(self):
        dump.table(self.db, "Users")

    def test_tables(self):
        dump.tables(self.db)