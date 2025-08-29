#!/usr/bin/env python3
import os
import subprocess
import sys


def restore_database(dump_file: str) -> bool:
    if not os.path.isfile(dump_file):
        print(f"File not found: {dump_file}")
        return False

    print("\nRestoring DB...")

    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "db2",
        "bash",
        "-c",
        "exec mysql --default-character-set=utf8mb4 -uroot -p${MYSQL_ROOT_PASSWORD} makeradmin",
    ]

    try:
        with open(dump_file, "rb") as sql_file:
            proc = subprocess.run(cmd, stdin=sql_file)
            if proc.returncode != 0:
                print("Restore failed.")
                sys.exit(proc.returncode)
    except Exception as e:
        print(f"Error: {e}")
        return False

    print("Done")
    return True


if __name__ == "__main__":
    # Prompt for confirmation before restoring
    while True:
        yn = input("This will delete your current database!! Are you sure you want to continue? [y/n] ").strip().lower()
        if yn in ("y", "yes"):
            break
        elif yn in ("n", "no"):
            sys.exit(0)
        else:
            print("Please answer yes or no.")

    sys.exit(0 if restore_database(sys.argv[1]) else 1)
