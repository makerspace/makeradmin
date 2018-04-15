#!/usr/bin/env python3
import argparse
import sys
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from destroyer.export import export_to_json


basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
    parser.add_argument("-o", "--out", default=None,
                        help="File where to store json.")
                        
    args = parser.parse_args()

    logger.info(f"connecting to {args.db}")

    db = create_engine(args.db)
    
    content = export_to_json(db)
    if args.out:
        with open(args.out, 'w') as w:
            logger.info(f"writing json dump to {args.out}")
            w.write(content)
    else:
        print(content)
    
    return
   
    
if __name__ == '__main__':

    main()
    