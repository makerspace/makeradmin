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


class settable_wrapper(object):
    """Really ugly wrapper for making objects hashable and comparable so that they can be converted to 'set'"""

    def __init__(self, obj):
        try:
            repr(obj)
        except Exception as e:
            logging.error(f"Could not 'repr' the object {obj}, and thus not hash it")
            raise e
        self.obj = obj

    def __getattr__(self, attr):
        try:
            return getattr(self.obj, attr)
        except Exception as e:
            raise e

    def __hash__(self):
        return hash(str(self))

    def assert_arguments_are_class_instances(func):
        def wrapper(*args):
            for arg in args:
                assert isinstance(arg, settable_wrapper), "Can only compare 'settable_wrapper' objects"
            return func(*args)
        return wrapper

    @assert_arguments_are_class_instances
    def __lt__(self, other):
        return repr(self) < repr(other)

    @assert_arguments_are_class_instances
    def __eq__(self, other):
        return self.obj == other.obj

    def __repr__(self):
        return repr(self.obj)

    def __str__(self):
        return str(self.obj)


def monkeypatch_settable(obj):
    try:
        hash(obj)
    except TypeError as e:
        obj = settable_wrapper(obj)
    finally:
        return obj


def monkeypatch_settable_for_list(list_obj):
    return [monkeypatch_settable(i) for i in list_obj]


def print_diff(old, new):
    
    # Sanity checking tables and colums should be same.
    assert(set(old.keys()) == set(new.keys()))
    
    tables = sorted(old.keys())
    
    for table in tables:
        old_table = old[table]
        new_table = new[table]
        assert(old_table['columns'] == new_table['columns'])
        
        # Check for duplicates or algorithm won't work.
        
        old_rows = monkeypatch_settable_for_list(old_table['rows'])
        old_set = set(old_rows)
        assert(len(old_rows) == len(set(old_rows)))
        
        new_rows = monkeypatch_settable_for_list(new_table['rows'])
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
    