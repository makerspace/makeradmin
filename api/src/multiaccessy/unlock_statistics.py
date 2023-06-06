import collections
from datetime import datetime, timedelta
import sqlite3

import pytz

from multiaccessy.accessy import Access, AccessyDoor


def dt2unix(dt: datetime) -> int:
    return int(dt.timestamp())


unix_time_0 = datetime(1970, 1, 1, tzinfo=pytz.UTC)
def unix2dt(unixtime: int) -> datetime:
    return unix_time_0 + timedelta(seconds=unixtime)


def ensure_init_db(con: sqlite3.Connection):
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS
    doors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accessy_id TEXT UNIQUE ON CONFLICT ABORT, -- assetPublicationId in Accessy
        name TEXT
    );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS
    unlocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        door INTEGER REFERENCES doors ( id ),
        person TEXT,
        unixtime INTEGER,
        CONSTRAINT timecombo UNIQUE (
            door, person, unixtime
        )
    );""")

    con.commit()


def ensure_door_exists(con: sqlite3.Connection, door: AccessyDoor) -> str:
    """ Returns the change reason (if any) """

    cur = con.cursor()

    cur.execute("""
    SELECT accessy_id, name
    FROM doors
    WHERE accessy_id = :id
    ;""", dict(id=door.id))
    result = cur.fetchone()
    door_exists = result is not None

    if not door_exists:
        cur.execute("""
        INSERT OR IGNORE INTO doors
        ( accessy_id, name )
        VALUES ( :id, :name )
        ;""", dict(id=door.id, name=door.name))
        con.commit()
        return f"Adding new door {door.name!r}"
    elif (result_door_name := result[1]) != door.name:
        cur.execute("""
        UPDATE doors
        SET name = :name
        WHERE accessy_id = :id
        ;""", dict(id=door.id, name=door.name))
        con.commit()
        return f"The door name has changed! Old name: {result_door_name}. New name: {door.name}"
    
    return ""


def insert_accesses(con: sqlite3.Connection, accesses: list[Access]) -> int:
    """ Returns the number of new rows inserted into DB (only unique ones). """
    cur = con.cursor()
    cur.executemany("""
    INSERT OR IGNORE
    INTO unlocks (
        door, person, unixtime
    ) SELECT doors.id, :person, :unixtime
    FROM doors
    WHERE doors.accessy_id = :accessy_door_id
    ;""", (dict(accessy_door_id=access.door.id, person=access.name, unixtime=dt2unix(access.dt)) for access in accesses))
    con.commit()
    return cur.rowcount


def select_accesses(con: sqlite3.Connection) -> list[Access]:
    cur = con.cursor()

    SqlResult = collections.namedtuple("SqlResult", "door_id, door_name, person, unixtime")
    cur.execute("""
    SELECT doors.accessy_id, doors.name, unlocks.person, unlocks.unixtime
    FROM unlocks
    JOIN doors ON doors.id = unlocks.door
    ;""")
    results = [SqlResult(*d) for d in cur.fetchall()]

    return list(Access(unix2dt(r.unixtime), r.person, AccessyDoor(r.door_id, r.door_name)) for r in results)
