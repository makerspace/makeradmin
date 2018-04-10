#!/usr/bin/env python3
import argparse
import os
import sys
import pyodbc
from logging import basicConfig, INFO, getLogger

from sqlalchemy import create_engine, MetaData

windows = os.name == 'nt'


basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db", default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
                        
    args = parser.parse_args()

    logger.info(f"connecting to {args.db}")

    engine = create_engine(args.db)
    meta = MetaData()
    meta.reflect(bind=engine)

    for table in meta.tables:
        print(table)
    #
    # connection = pyodbc.connect(Trusted_Connection='yes',
    #                             driver='{SQL Server}',
    #                             server='(local)\SQLEXPRESS',
    #                             database='MultiAccess')
    #
    # cursor = connection.cursor()
    # cursor.execute("select * from Users")
    # for row in cursor.fetchall():
    #     print(row)
    #
    # cursor.tables()
    # for row in cursor.fetchall():
    #     print(row.table_name)
    
    
if __name__ == '__main__':

    try:
        main()
        if windows:
            input("Export finished, enter to close: ")
    except Exception as e:
        if windows:
            logger.exception(e)
            input("Program failed, enter to close: ")
        else:
            raise
