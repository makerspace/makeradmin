#!/usr/bin/env python3
import argparse
import sys
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
                        
    args = parser.parse_args()

    logger.info(f"connecting to {args.db}")

    engine = create_engine(args.db)
    Session = sessionmaker(bind=engine)
    session = Session()
    return

"""
API data:
member_id      debug  int
member_number  use    int
firstname      info   string
lastname       info   string
key_id         debug  int
rfid_tag       use    string
status         use    bool
end_timestamp  use    string timestamp z
"""

if __name__ == '__main__':

    main()
