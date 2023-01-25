import collections
from datetime import datetime, timedelta
import sqlite3
import sys

from multiaccessy.accessy import accessy_session, Access, AccessyDoor
from service.config import config


con = sqlite3.connect("accessy.db")
cur = con.cursor()


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
        assetPublicationId TEXT UNIQUE ON CONFLICT ABORT,
        name TEXT
    );""")

    # cur.execute("""
    # CREATE TABLE IF NOT EXISTS
    # members (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     uuid TEXT UNIQUE ON CONFLICT ABORT,
    #     name TEXT
    # );""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS
    unlocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        door INTEGER REFERENCES doors ( id ),
        person TEXT,
        -- person INTEGER REFERENCES members ( id ),
        unixtime INTEGER,
        CONSTRAINT timecombo UNIQUE (
            door, person, unixtime
        )
    );""")

    con.commit()


def ensure_door_exists(con: sqlite3.Connection, door: AccessyDoor):
    cur = con.cursor()

    cur.execute("""
    SELECT assetPublicationId, name
    FROM doors
    WHERE assetPublicationId = :id
    ;""", dict(id=door.id))
    result = cur.fetchone()
    door_exists = result is not None

    if not door_exists:
        cur.execute("""
        INSERT OR IGNORE INTO doors
        ( assetPublicationId, name )
        VALUES ( :id, :name )
        ;""", dict(id=door.id, name=door.name))
        con.commit()
    elif (result_door_name := result[1]) != door.name:
        print(f"The door name has changed! Old name: {result_door_name}. New name: {door.name}")
        cur.execute("""
        UPDATE SET name = :name
        FROM doors
        WHERE assetPublicationId = :id
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
    WHERE doors.assetPublicationId = :door_id
    ;""", (dict(door_id=access.door.id, person=access.name, unixtime=dt2unix(access.dt)) for access in accesses))
    con.commit()
    print(f"Updated {cur.rowcount} rows")
    return cur.rowcount


ensure_init_db(con)

ACCESSY_SESSION_TOKEN = config.get("ACCESSY_SESSION_TOKEN")
accessy_session.session_token = ACCESSY_SESSION_TOKEN
accessy_session.session_token_token_expires_at = datetime.now() + timedelta(days=1)


doors = accessy_session.get_all_doors()

for door in doors:
    ensure_door_exists(con, door)

accesses: list[Access] = []
for door in doors:
    accesses = accessy_session.get_all_accesses(door)
    insert_accesses(con, accesses)

sys.exit(0)


accesses_per_door = collections.Counter(a.door.name for a in accesses)
print(f"Accesses per door: {accesses_per_door}")

accesses_per_date = collections.Counter(a.dt.date() for a in accesses)
print(f"Accesses per date: {accesses_per_date}")

weekday_lookup = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
accesses_per_day = collections.Counter(weekday_lookup[a.dt.date().weekday()] for a in accesses)
print(f"Accesses per day: {accesses_per_day}")

people_accesses_per_date = collections.defaultdict(lambda: collections.Counter())
for access in accesses:
    people_accesses_per_date[access.dt.date()].update({access.name: 1})
print(f"People accesses per date {people_accesses_per_date}")

unique_people_per_date = {d: len(people_accesses_per_date[d].keys()) for d in people_accesses_per_date.keys()}
print(f"Unique people per date {unique_people_per_date}")

people_accesses_per_day = collections.defaultdict(lambda: collections.Counter())
for access in accesses:
    people_accesses_per_day[weekday_lookup[access.dt.weekday()]].update({access.name: 1})
print(f"People accesses per day {people_accesses_per_day}")

unique_people_per_day = {d: len(people_accesses_per_day[d].keys()) for d in people_accesses_per_day.keys()}
print(f"Unique people per day {unique_people_per_day}")
