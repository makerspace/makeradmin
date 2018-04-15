import unittest
from src import db_helper

class Test(unittest.TestCase):
    def test_CreateDefaultEngine(self):
        import sqlalchemy
        self.assertIsInstance(db_helper.create_default_engine(), sqlalchemy.engine.base.Engine)