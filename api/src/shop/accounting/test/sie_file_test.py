from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from typing import Dict, List, Optional, Tuple
from unittest import TestCase

from shop.accounting.sie_file import (
    convert_to_sie_format,
    get_header,
    transaction_string,
    write_to_sie_file,
)
from shop.accounting.verification import Verification

logger = getLogger("makeradmin")


class SieFileTest(TestCase):
    def test_convert_to_sie(self) -> None:
        pass

    def test_write_sie_file(self) -> None:
        pass
