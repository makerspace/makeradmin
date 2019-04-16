import sys

from multi_access.tui import Tui
from test.base import BaseTest


class Test(BaseTest):
    
    def test_fatal_methods_raises_system_exit(self):
        ui = Tui()
        with self.assertRaises(SystemExit): ui.fatal__error("err")
        with self.assertRaises(SystemExit): ui.fatal__problem_members([])

    def test_info_methods_does_not_block_execution(self):
        ui = Tui()
        ui.info__progress("msg")
        