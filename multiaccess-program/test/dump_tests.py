import unittest
from src import dump
from src import db_helper

class Test(unittest.TestCase):
    def setUp(self):
        self.db = db_helper.create_default_engine()

    def test_table(self):
        dump.table(self.db, "Users")

    def test_tables(self):
        dump.tables(self.db)