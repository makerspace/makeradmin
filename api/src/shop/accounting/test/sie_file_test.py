from logging import getLogger
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest import TestCase

from shop.accounting.verification import Verification
from shop.accounting.sie_file import (
    get_header,
    transaction_string,
    convert_to_sie_format,
    write_to_sie_file,
)

logger = getLogger("makeradmin")


class SieFileTest(TestCase):
    def test_convert_to_sie(self) -> None:
        pass

    def test_write_sie_file(self) -> None:
        pass
