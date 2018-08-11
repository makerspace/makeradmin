from datetime import datetime, date

from multi_access.util import cet_to_utc, dt_format, utc, cet, date_parse, to_cet_23_59_59
from test.base import BaseTest


class Test(BaseTest):
    
    def test_cet_to_utc(self):
        self.assertEqual(datetime(2018, 5, 22, 10), cet_to_utc(datetime(2018, 5, 22, 12)))
        self.assertEqual(datetime(2018, 1, 22, 10), cet_to_utc(datetime(2018, 1, 22, 11)))

    def test_to_cet(self):
        self.assertEqual(datetime(2018, 5, 22, 23, 59, 59), to_cet_23_59_59(date(2018, 5, 22)))
        self.assertEqual(datetime(2018, 1, 22, 23, 59, 59), to_cet_23_59_59(date(2018, 1, 22)))
        self.assertEqual(datetime(2018, 5, 22, 23, 59, 59), to_cet_23_59_59(date(2018, 5, 22)))
        self.assertEqual(None, to_cet_23_59_59(None))

    def test_dt_format(self):
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10)))
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10, tzinfo=utc)))
        with self.assertRaises(AssertionError): dt_format(datetime(2018, 5, 22, 10, tzinfo=cet))

    def test_dt_parse(self):
        self.assertEqual(date(2018, 5, 22), date_parse("2018-05-22"))
        self.assertEqual(date(2018, 5, 22), date_parse("2018-05-22"))
        self.assertEqual(None, date_parse(None))

