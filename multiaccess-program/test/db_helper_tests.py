import unittest
import src.db_helper as db_helper

class Test(unittest.TestCase):
    def test_CreateDefaultEngine(self):
        import sqlalchemy
        self.assertIsInstance(db_helper.create_default_engine(), sqlalchemy.engine.base.Engine)