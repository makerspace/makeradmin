#!/usr/bin/env python3
import argparse
import json
import pickle
import re
import sys
from logging import basicConfig, INFO, getLogger
from os import path, listdir

logger = getLogger("makeradmin")


def read_dump(filename):
    if filename.endswith(".pkl"):
        with open(filename, "rb") as f:
            return pickle.load(f)
    elif filename.endswith(".json"):
        with open(filename, "r", encoding="utf8") as f:
            return json.load(f)
    else:
        raise Exception(f"unknown filetype {filename}")


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

    directory = args.in_dir
    
    def use_file(filename):
        if not path.isfile(path.join(directory, filename)):
            return False
        m = re.match(r'dump-(\d+).' + args.extension, filename)
        if not m:
            return 0
        return int(m.group(1))
    
    filenames = [path.join(directory, f) for f in sorted(listdir(directory)) if use_file(f)]
    
    prev_dump = None
    for filename in filenames:
        logger.info(f'loading dump file {filename}')
        next_dump = read_dump(filename)
        pass

    
if __name__ == '__main__':
    main()
    