#!/usr/bin/env python3

import os
import sys
import pyodbc
from logging import basicConfig, INFO, getLogger


windows = os.name == 'nt'


basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)


logger = getLogger("makeradmin")


def main():

    connection = pyodbc.connect(Trusted_Connection='yes',
                                driver='{SQL Server}',
                                server='(local)\SQLEXPRESS',
                                database='MultiAccess')
    
    cursor = connection.cursor()
    cursor.execute("select * from Users")
    for row in cursor.fetchall():
        print(row)

    cursor.tables()
    for row in cursor.fetchall():
        print(row.table_name)
    
    
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
