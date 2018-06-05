from datetime import datetime, timezone, timedelta

from multi_access.util import cet_to_utc, dt_format, utc, cet, dt_parse, to_cet
from test.base import BaseTest


class Test(BaseTest):
    
    def test_cet_to_utc(self):
        self.assertEqual(datetime(2018, 5, 22, 10), cet_to_utc(datetime(2018, 5, 22, 12)))
        self.assertEqual(datetime(2018, 1, 22, 10), cet_to_utc(datetime(2018, 1, 22, 11)))

    def test_to_cet(self):
        self.assertEqual(datetime(2018, 5, 22, 10),
                         to_cet(datetime(2018, 5, 22, 8, tzinfo=timezone(timedelta(hours=0)))))
        self.assertEqual(datetime(2018, 1, 22, 10),
                         to_cet(datetime(2018, 1, 22, 9, tzinfo=timezone(timedelta(hours=0)))))
        self.assertEqual(datetime(2018, 5, 22, 10),
                         to_cet(datetime(2018, 5, 22, 10, tzinfo=timezone(timedelta(hours=2)))))
        self.assertEqual(None, to_cet(None))

    def test_dt_format(self):
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10)))
        self.assertEqual("2018-05-22T10:00:00.000000Z", dt_format(datetime(2018, 5, 22, 10, tzinfo=utc)))
        with self.assertRaises(AssertionError): dt_format(datetime(2018, 5, 22, 10, tzinfo=cet))

    def test_dt_parse(self):
        self.assertEqual(datetime(2018, 5, 22, 10, tzinfo=timezone(timedelta(hours=2))),
                         dt_parse("2018-05-22T10:00:00+02:00"))
        self.assertEqual(datetime(2018, 5, 22, 10, tzinfo=timezone(timedelta(hours=-1))),
                         dt_parse("2018-05-22T10:00:00-01:00"))
        self.assertEqual(None, dt_parse(None))

