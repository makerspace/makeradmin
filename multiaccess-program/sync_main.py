#!/usr/bin/env python3
import argparse
import sys
import psutil
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from multi_access.auth import MakerAdminSimpleTokenAuth
from multi_access.maker_admin import fetch_maker_admin_members
from multi_access.multi_access import create_end_timestamp_diff, get_multi_access_members
from multi_access.tui import Tui

logger = getLogger("makeradmin")


def check_multi_access_running():
    for process in psutil.process_iter():
        if 'multiaccess' in process.name().lower():
            return True
    return False


def sync(ui, session, maker_admin_url):
    
    # Exit if MultiAccess is running
    
    ui.info__progress("checking for running MultiAccess")
    if check_multi_access_running():
        ui.fatal__error("looks like MultiAccess is running, please exit MultiAccess and run again")
    ui.info__progress("found no running MultiAccess")
    
    # Fetch from MakerAdmin
    
    ui.info__progress(f"getting member list from {maker_admin_url}")
    auth = MakerAdminSimpleTokenAuth()
    maker_admin_members = fetch_maker_admin_members(maker_admin_url, auth)
    ui.info__progress(f"got {len(maker_admin_members)} members")
    
    # Fetch relevant data from db and diff it
    
    multi_access_members = get_multi_access_members(session)
    problem_members = [m for m in multi_access_members if m.problems]
    if problem_members:
        ui.fatal__problem_members(problem_members)
    
    ui.info__progress('diffing multi access users against maker admin members')
    diff = create_end_timestamp_diff(multi_access_members, maker_admin_members)
    print(diff)
    
    # Present diff of what will be changed
    # Preform changes
    
    return
    

def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
                stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
    parser.add_argument("-u", "--maker-admin-url",
                        default='https://makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("--maker-admin-credentials-filename",
                        help="Filename where credentials for maker admin are stored.")
                        
    args = parser.parse_args()

    with Tui() as ui:

        ui.info__progress(f"connecting to {args.db}")
    
        engine = create_engine(args.db)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        sync(ui, session, args.maker_admin_url)


if __name__ == '__main__':

    main()
