#!/usr/bin/env python3
import argparse
import json
import pickle
import re
import sys
from logging import basicConfig, INFO, getLogger
from os import path, listdir
from multi_access.dump.dump import from_file

logger = getLogger("makeradmin")


def print_diff(old, new):
    
    # Sanity checking tables and colums should be same.
    assert(set(old.keys()) == set(new.keys()))
    
    tables = sorted(old.keys())
    
    for table in tables:
        old_table = old[table]
        new_table = new[table]
        assert(old_table['columns'] == new_table['columns'])
        
        # Check for duplicates or algorithm won't work.
        
        old_rows = old_table['rows']
        old_set = set(old_rows)
        assert(len(old_rows) == len(set(old_rows)))
        
        new_rows = new_table['rows']
        new_set = set(new_rows)
        assert(len(new_rows) == len(set(new_rows)))
    
        # Check for added and removed rows.
        
        added = new_set - old_set
        removed = old_set - new_set
        if added or removed:
            print(f"table {table} diffing, columns {old_table['columns']}")
            diff = sorted([('ADD', d) for d in added] + [('DEL', d) for d in removed], key=lambda x: x[1])
            for what, d in diff:
                print(f"   {what}: {d!r}")
        

def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(pathname)s:%(lineno)d]: %(message)s',
                stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser()
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
        next_dump = from_file(filename)
        if prev_dump:
            logger.info(f'diffing to previous dump')
            print_diff(prev_dump, next_dump)
        prev_dump = next_dump
    
    
if __name__ == '__main__':
    main()
    