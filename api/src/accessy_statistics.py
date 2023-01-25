from datetime import datetime, timedelta
import sqlite3

from multiaccessy.accessy import accessy_session, Access, AccessyDoor
from multiaccessy.unlock_statistics import ensure_init_db, ensure_door_exists, insert_accesses
from service.config import config


def main():
    con = sqlite3.connect("accessy.db")
    ensure_init_db(con)

    ACCESSY_SESSION_TOKEN = config.get("ACCESSY_SESSION_TOKEN")
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
    

if __name__ == "__main__":
    main()
