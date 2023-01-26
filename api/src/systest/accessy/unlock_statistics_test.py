from datetime import datetime
import sqlite3
from unittest import TestCase

import pytz

from multiaccessy.accessy import AccessyDoor, Access
from multiaccessy.unlock_statistics import (ensure_init_db, ensure_door_exists,
    insert_accesses, select_accesses, unix_time_0, unix2dt, dt2unix)


class HelperTest(TestCase):
    def test_convert_unix_t0(self):
        self.assertEqual(unix2dt(0), unix_time_0)

    def test_convert_unix_convert_back_and_forth(self):
        unix0 = unix2dt(0)
        self.assertEqual(dt2unix(unix0), 0)


class AccessyStatisticsTest(TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.test_door = AccessyDoor("uuid-door", "Test door")
        self.access = Access(unix_time_0, "FirstName LastName", self.test_door)
        ensure_init_db(self.con)

    def tearDown(self) -> None:
        self.con.close()

    def test_init_again(self):
        ensure_init_db(self.con)

    def test_add_door(self):
        change = ensure_door_exists(self.con, AccessyDoor("asd", "Test door"))
        self.assertIn("add", change.lower())

    def test_add_door_twice(self):
        ensure_door_exists(self.con, self.test_door)
        change = ensure_door_exists(self.con, self.test_door)
        self.assertEqual("", change)

    def test_add_door_changed_name(self):
        ensure_door_exists(self.con, self.test_door)
        self.test_door.name = "New name"
        change = ensure_door_exists(self.con, self.test_door)
        self.assertIn("changed", change.lower())
    
    def test_add_access_without_door(self):
        inserts = insert_accesses(self.con, [self.access])
        self.assertEqual(inserts, 0)
    
    def test_add_access_with_door(self):
        ensure_door_exists(self.con, self.test_door)
        inserts = insert_accesses(self.con, [self.access])
        self.assertEqual(inserts, 1)
    
    def test_add_access_duplicate(self):
        ensure_door_exists(self.con, self.test_door)
        _ = insert_accesses(self.con, [self.access])
        inserts = insert_accesses(self.con, [self.access])
        self.assertEqual(inserts, 0)
    
    def test_get_back_access(self):
        ensure_door_exists(self.con, self.test_door)
        insert_accesses(self.con, [self.access])
        accesses = select_accesses(self.con)
        self.assertEqual(set(accesses), {self.access})
    
    def test_get_back_accesses(self):
        ensure_door_exists(self.con, self.test_door)
        now = datetime.now(tz=pytz.UTC)
        access2 = Access(now, "Person2", self.test_door)
        insert_accesses(self.con, [self.access, access2])
        accesses = select_accesses(self.con)
        access2.dt = now.replace(microsecond=0)
        self.assertEqual(set(accesses), {self.access, access2})

