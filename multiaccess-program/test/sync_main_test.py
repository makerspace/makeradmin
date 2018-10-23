from unittest import mock

from multi_access.tui import Tui
from sync_main import is_multi_access_running
from test.base import BaseTest


class Test(BaseTest):

    def test_multi_access_is_running_test(self):
        with mock.patch('psutil.Process.name', return_value='MultiAccess.exe'):
            self.assertTrue(is_multi_access_running())

        with mock.patch('psutil.Process.name', return_value='multiaccess.exe'):
            self.assertTrue(is_multi_access_running())

    def test_multi_access_is_not_running_test(self):
        with mock.patch('psutil.Process.name', return_value='multi_access_sync.exe'):
            self.assertFalse(is_multi_access_running())
