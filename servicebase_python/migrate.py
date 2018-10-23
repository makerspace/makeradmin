#!/usr/bin/env python3

import service
import os
import sys

check = len(sys.argv) > 1 and sys.argv[1] == "--assert-up-to-date"

db, gateway, debug = service.read_config()
db.connect()

green = "\033[32m"
red = "\033[31m"
reset = "\033[0m"
table_prefix = os.environ["TABLE_PREFIX"]
if table_prefix is None or table_prefix == "":
    print("No table prefix set (TABLE_PREFIX environment variable)")
    exit(1)

migrations_table = f"migrations_{table_prefix}"
with db.cursor() as cur:
    # Disable 'table already exists' warning
    cur.execute("SET sql_notes = 0")
    # Create the migrations table
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{migrations_table}` (
            `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
            `migration` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
            `batch` int(11) NOT NULL,
            PRIMARY KEY (`id`)
        )
    """)
    cur.execute("SET sql_notes = 1")

    # Find all migration files (it is assumed that they are named as numbers)
    files = [int(n.split(".sql")[0]) for n in os.listdir("database") if n.endswith(".sql")]
    # Make sure they are sorted
    files.sort()
    anyMigrations = False
    for migration in files:
        name = str(migration)
        sql = open("database/" + name + ".sql").read()

        # Divide the sql query into a number of commands
        batches = [b.strip() for b in sql.split(";") if b.strip() != ""]

        # Check how many (if any) commands from this file have been previously executed
        cur.execute(f"SELECT batch FROM `{migrations_table}` WHERE migration=%s", (name,))
        batch = cur.fetchone()
        if batch is None:
            cur.execute(f"INSERT INTO `{migrations_table}` (migration,batch) VALUES (%s,%s)", (name, 0))
            batch = 0
        else:
            batch = batch[0]

        for i in range(batch, len(batches)):
            if check:
                print(red + "This module has database migrations to run. Please run `make init-db` first." + reset)
                exit(1)

            anyMigrations = True
            print(green + "Running migration " + name + " batch " + str(i) + "..." + reset)
            print(batches[i])
            cur.execute(batches[i])
            cur.execute(f"UPDATE `{migrations_table}` SET batch=%s WHERE migration=%s", (i+1,name))

    if not anyMigrations and not check:
        print(green + "Nothing to migrate." + reset)
