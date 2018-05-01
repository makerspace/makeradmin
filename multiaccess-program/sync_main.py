#!/usr/bin/env python3
import argparse
import sys
import psutil
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from multi_access.auth import MakerAdminSimpleTokenAuth
from multi_access.maker_admin import fetch_maker_admin_members
from multi_access.multi_access import get_multi_access_members

basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def check_multi_access_running():
    for process in psutil.process_iter():
        if 'multiaccess' in process.name().lower():
            return True
    return False


def main():

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

    logger.info(f"connecting to {args.db}")

    engine = create_engine(args.db)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Exit if MultiAccess is running
    
    logger.info("checking for running MultiAccess")
    if check_multi_access_running():
        logger.error("looks like MultiAccess is running, please exit MultiAccess and run again")
        return
    logger.info("found no running MultiAccess")
    
    # Fetch from MakerAdmin
    
    logger.info(f"getting member list from {args.maker_admin_url}")
    auth = MakerAdminSimpleTokenAuth(access_token="FDyVvBXugvX90bnNeBpwlWbUlkPG5Mp6")
    try:
        maker_admin_members = fetch_maker_admin_members(args.maker_admin_url, auth)
    except Exception as e:
        logger.exception("could not get member infos from maker admin")
        return
    logger.info(f"got {len(maker_admin_members)} members")
        
    # Fetch relevant data from db
    
    multi_access_members = get_multi_access_members(session)
    
    # Present diff of what will be changed
    # Perorm changes
    
    return


if __name__ == '__main__':

    main()
