#!/usr/bin/env python3
import argparse
import sys
import psutil
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from multi_access.maker_admin import MakerAdminClient
from multi_access.multi_access import create_end_timestamp_diff, get_multi_access_members, update_diffs
from multi_access.tui import Tui

logger = getLogger("makeradmin")


def check_multi_access_running(ui):
    ui.info__progress("checking for running MultiAccess")
    for process in psutil.process_iter():
        if 'multiaccess' in process.name().lower():
            ui.fatal__error("looks like MultiAccess is running, please exit MultiAccess and run again")
    ui.info__progress("found no running MultiAccess")


def sync(session=None, client=None, ui=None, customer_id=16):
    
    # Exit if MultiAccess is running
    
    check_multi_access_running(ui)
    
    # Fetch from MakerAdmin
    
    ma_members = client.fetch_members(ui)
    
    # Fetch relevant data from db and diff it
    
    db_members = get_multi_access_members(session, customer_id)
    problem_members = [m for m in db_members if m.problems]
    if problem_members:
        ui.fatal__problem_members(problem_members)
    
    ui.info__progress('diffing multi access users against maker admin members')
    diffs = create_end_timestamp_diff(db_members, ma_members)
    
    if not diffs:
        ui.info__progress('nothing to update')
        return
    
    # Present diff of what will be changed

    ui.prompt__update_db(heading=f'the following {len(diffs)} updates will be made',
                         lines=[d.describe_update() for d in diffs])
    
    # Preform changes
    
    update_diffs(session, ui, diffs)
    ui.info__progress('finished updating db')
    
    return
    

def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
                stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("-m", "--members-filename", default=None,
                        help="Provide members in a file instead of fetching from make admin.")
    parser.add_argument("--maker-admin-credentials-filename",
                        help="Filename where credentials for maker admin are stored. Should contain a two lines"
                             " with username on the first and password on the second.")
                        
    args = parser.parse_args()

    with Tui() as ui:
        client = MakerAdminClient(ui=ui, base_url=args.maker_admin_base_url, members_filename=args.members_filename)

        ui.info__progress(f"connecting to {args.db}")
        engine = create_engine(args.db)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        sync(session=session, ui=ui, client=client)


if __name__ == '__main__':

    main()
