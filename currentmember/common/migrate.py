#!/usr/bin/env python3

import argparse
from mygrations.mygrate import mygrate
import service
import os
from io import StringIO
import sys

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('-f', dest='force', action='store_true', help='Ignore errors/warnings and execute command anyway')
args = parser.parse_args()

db, gateway, debug = service.read_config()

with open(".env", "w") as f:
    f.write("DB_HOSTNAME={}\nDB_USERNAME={}\nDB_PASSWORD={}\nDB_DATABASE={}".format(db.host.split(":")[0], db.user, db.password, db.name))

with open("mygrate.conf", "w") as f:
    f.write("hostname_key=DB_HOSTNAME\nusername_key=DB_USERNAME\npassword_key=DB_PASSWORD\ndatabase_key=DB_DATABASE\nfiles_directory=database")

# The mygrations module is not well behaved and just spits everything out on stdout, so we have to redirect it
stdout_ = sys.stdout  # Keep track of the previous value.
plan = StringIO()
sys.stdout = plan

# load up a mygrate object
my = mygrate("plan", {
    "force": args.force,
    "version": False,
    "env": ".env",
    "config": "mygrate.conf",
})

# and execute
my.execute()

sys.stdout = stdout_  # restore the previous stdout.

os.remove(".env")
os.remove("mygrate.conf")

planStr = plan.getvalue().strip()
if "Errors found" in planStr:
    print(planStr)
    exit(1)

db.connect()
with db.cursor() as c:
    for statement in planStr.split(";"):
        if statement.strip() != "":
            print(statement)
            c.execute(statement)
