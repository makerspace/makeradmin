#!/usr/bin/env python3
import argparse
import sys
from logging import basicConfig, INFO, getLogger


logger = getLogger("makeradmin")


def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db",
                        default='mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server',
                        help="SQL Alchemy db engine spec.")
    parser.add_argument("-i", "--in-dir", default='.',
                        help="Dir where diff files are stored.")
    parser.add_argument("-e", "--extension", default='pkl',
                        help="Format pkl or json.")
    args = parser.parse_args()

    
if __name__ == '__main__':
    main()
    