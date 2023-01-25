from argparse import ArgumentParser
from enum import Enum
from datetime import datetime, timedelta
import sqlite3

from multiaccessy.accessy import accessy_session, Access, AccessyDoor
from multiaccessy.unlock_statistics import ensure_init_db, ensure_door_exists, insert_accesses
from service.config import config


def fetch_accessy(con: sqlite3.Connection):
    ensure_init_db(con)

    ACCESSY_SESSION_TOKEN = config.get("ACCESSY_SESSION_TOKEN")
    # Use cached token if it exists
    accessy_session.session_token = ACCESSY_SESSION_TOKEN
    accessy_session.session_token_token_expires_at = datetime.now() + timedelta(days=1)

    doors = accessy_session.get_all_doors()
    for door in doors:
        ensure_door_exists(con, door)

    accesses: list[Access] = []
    for door in doors:
        print(f"Getting unlocks for door {door.name!r}")
        accesses = accessy_session.get_all_accesses(door)
        row_updates = insert_accesses(con, accesses)
        print(f"    {row_updates} new unlocks")


class Modes(Enum):
    fetch = "fetch"
    
    def __repr__(self):
        return self.name


def main():
    parser = ArgumentParser("Fetch data about door unlocks from Accessy and store in local database")
    parser.add_argument("--database", default="accessy.db", help="Name of sqlite3 database to use")
    parser.add_argument("--mode", type=Modes, choices=list(Modes), default=Modes.fetch, help="Mode to run program in")
    args = parser.parse_args()

    con = sqlite3.connect(args.database)

    if args.mode == Modes.fetch:
        fetch_accessy(con)
    else:
        raise RuntimeError(f"Unhandled mode {args.mode}")
    

if __name__ == "__main__":
    main()
