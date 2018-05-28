from datetime import datetime

from multi_access.util import cet_to_utc, dt_format, utc, cet, dt_parse
from test.base import BaseTest


class Test(BaseTest):
    
    def cet_to_utc(self):
        self.assertEqual(datetime(2018, 5, 22, 10), cet_to_utc(datetime(2018, 5, 22, 12)))
        self.assertEqual(datetime(2018, 1, 22, 10), cet_to_utc(datetime(2018, 1, 22, 11)))

    def test_dt_format(self):
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10)))
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10, tzinfo=utc)))
        with self.assertRaises(AssertionError): dt_format(datetime(2018, 5, 22, 10, tzinfo=cet))

    def test_dt_parse(self):
        self.assertEqual(datetime(2018, 5, 22, 10), dt_parse("2018-05-22T10:00:00.000000Z"))
