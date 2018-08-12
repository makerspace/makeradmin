#!/usr/bin/env python3
import argparse
import sys

import psutil
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from multi_access.maker_admin import MakerAdminClient
from multi_access.multi_access import get_multi_access_members, update_diffs, \
    UpdateMember, AddMember, BlockMember
from multi_access.tui import Tui

try:
    from source_revision import source_revision
except ImportError:
    source_revision = 'unknown'

logger = getLogger("makeradmin")


WHAT_ORDERS = 'orders'
WHAT_UPDATE = 'update'
WHAT_ADD = 'add'
WHAT_BLOCK = 'block'
WHAT_ALL = {WHAT_ORDERS, WHAT_UPDATE, WHAT_ADD, WHAT_BLOCK}


def is_multi_access_running():
    for process in psutil.process_iter():
        if 'multiaccess' in process.name().lower():
            return True

    return False


def sync(session=None, client=None, ui=None, customer_id=None, authority_id=None, what=None, ignore_running=False):
    what = what or WHAT_ALL
    
    # Exit if MultiAccess is running
    
    if not ignore_running:
        ui.info__progress("checking for running MultiAccess")
        if is_multi_access_running():
            ui.info__progress("looks like MultiAccess is running, please exit MultiAccess and run again")
            return

    # Log in to the MakerAdmin server unless we are already logged in
    if not client.is_logged_in():
        while not client.login():
            pass

    # Run actions on MakerAdmin (ship orders and update key timestamps)

    if WHAT_ORDERS in what:
        client.ship_orders(ui)

    # Fetch from MakerAdmin
    
    ma_members = client.fetch_members(ui)
    
    # Fetch relevant data from db and diff it
    
    db_members = get_multi_access_members(session, ui, customer_id)
    
    # Diff maker data.
    
    ui.info__progress('diffing multi access users against maker admin members')
    diffs = []
    if WHAT_UPDATE in what:
        diffs += UpdateMember.find_diffs(db_members, ma_members)
    if WHAT_ADD in what:
        diffs += AddMember.find_diffs(db_members, ma_members)
    if WHAT_BLOCK in what:
        diffs += BlockMember.find_diffs(db_members, ma_members)
    
    if not diffs:
        ui.info__progress('nothing to update')
        return
    
    # Present diff of what will be changed

    ui.prompt__update_db(heading=f'the following {len(diffs)} changes will be made',
                         lines=[d.describe_update() for d in diffs])
    
    # Preform changes
    
    update_diffs(session, ui, diffs, customer_id=customer_id, authority_id=authority_id)
    ui.info__progress('finished updating db')
    
    return
    

def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
                stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser("Fetches member list from makeradmin.se or local file, then prompt user with"
                                     f" changes to make. Built from source revision {source_revision}.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
    parser.add_argument("-w", "--what", default=",".join(WHAT_ALL),
                        help=f"What to update, comma separated list."
                             f" '{WHAT_ORDERS}' tell maker admin to perform order actions before updating members."
                             f" '{WHAT_UPDATE}' will update end times and rfid_tag."
                             f" '{WHAT_ADD}' will add members in MultAccess."
                             f" '{WHAT_BLOCK}' will block members that should not have access."
                        )
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("-m", "--members-filename", default=None,
                        help="Provide members in a file instead of fetching from maker admin (same format as response"
                             " from maker admin).")
    parser.add_argument("-t", "--token", default="",
                        help="Provide token on command line instead of prompting for login.")
    parser.add_argument("--customer-id", default=16, type=int,
                        help="MultiAcces custoemr primary key to use to get and add users.")
    parser.add_argument("--authority-id", default=23, type=int,
                        help="MultiAcces authority primary key to add ny default to new users.")
    parser.add_argument("--ignore-running", action='store_true',
                        help="Ignore the check for if MultiAcces is running, do not use this.")
    
    args = parser.parse_args()

    what = args.what.split(',')
    for w in what:
        if w not in WHAT_ALL:
            raise argparse.ArgumentError(f"Unknown argument '{w}' to what.")

    with Tui() as ui:
        client = MakerAdminClient(ui=ui, base_url=args.maker_admin_base_url, members_filename=args.members_filename,
                                  token=args.token)

        ui.info__progress(f"connecting to {args.db}")
        engine = create_engine(args.db)

        while True:
            Session = sessionmaker(bind=engine)
            session = Session()
            
            sync(session=session, ui=ui, client=client, customer_id=args.customer_id, authority_id=args.authority_id,
                 ignore_running=args.ignore_running, what=what)

            session.close()

            input("press enter to update the database again")


if __name__ == '__main__':

    main()
