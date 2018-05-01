import unittest
from src import db_helper
import sqlalchemy


class Test(unittest.TestCase):
    
    def test_CreateDefaultEngine(self):
        self.assertIsInstance(db_helper.create_default_engine(), sqlalchemy.engine.base.Engine)
        