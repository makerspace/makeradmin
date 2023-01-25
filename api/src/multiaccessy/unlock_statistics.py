from datetime import datetime, timedelta
import sqlite3

from multiaccessy.accessy import Access, AccessyDoor


def dt2unix(dt: datetime) -> int:
    return int(dt.timestamp())


def unix2dt(unixtime: int) -> datetime:
    return datetime(1970, 1, 1) + timedelta(seconds=unixtime)


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


def ensure_door_exists(con: sqlite3.Connection, door: AccessyDoor):
    cur = con.cursor()

    cur.execute("""
    SELECT accessy_id, name
    FROM doors
    WHERE accessy_id = :id
    ;""", dict(id=door.id))
    result = cur.fetchone()
    door_exists = result is not None

    if not door_exists:
        print(f"Adding new door {door.name!r}")
        cur.execute("""
        INSERT OR IGNORE INTO doors
        ( accessy_id, name )
        VALUES ( :id, :name )
        ;""", dict(id=door.id, name=door.name))
        con.commit()
    elif (result_door_name := result[1]) != door.name:
        print(f"The door name has changed! Old name: {result_door_name}. New name: {door.name}")
        cur.execute("""
        UPDATE SET name = :name
        FROM doors
        WHERE accessy_id = :id
        ;""", dict(id=door.id, name=door.name))
        con.commit()


def insert_accesses(con: sqlite3.Connection, accesses: list[Access]) -> int:
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
