#!/usr/bin/env python3
import os
from datetime import datetime
from subprocess import PIPE, run


def backup_database() -> str:
    CURRENT_TIME = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
    EXPORT_PATH = "data/db_backup"
    FILENAME = f"db_{CURRENT_TIME}.sql"
    FILEPATH = f"/tmp/{FILENAME}"

    os.makedirs(EXPORT_PATH, exist_ok=True)

    # Get DB container ID
    result = run(["docker", "compose", "ps", "-q", "db2"], stdout=PIPE, check=True, text=True)
    DB_CONTAINER = result.stdout.strip()

    # Dump database inside container
    dump_cmd = f"mysqldump -p${{MYSQL_ROOT_PASSWORD}} --create-options --complete-insert --quote-names makeradmin >> {FILEPATH}"
    run(["docker", "compose", "exec", "db2", "bash", "-c", dump_cmd], check=True)

    # Copy dump file from container to host
    run(["docker", "cp", "--quiet", f"{DB_CONTAINER}:{FILEPATH}", EXPORT_PATH], check=True)

    # Remove dump file from container
    run(["docker", "compose", "exec", "db2", "bash", "-c", f"rm {FILEPATH}"], check=True)

    return os.path.join(EXPORT_PATH, FILENAME)


if __name__ == "__main__":
    exported_file = backup_database()
    size_bytes = os.path.getsize(exported_file)

    def human_readable_size(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.0f} {unit}"
            size /= 1024.0
        return f"{size:.0f} PB"

    print(f"Exported {human_readable_size(size_bytes)} to {exported_file}")
