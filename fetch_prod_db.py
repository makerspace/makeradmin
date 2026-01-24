#!/usr/bin/env python3
"""
Fetch production database and restore it locally.

This script:
1. Connects to production server via SSH
2. Runs the backup script to create a fresh database dump
3. Downloads the backup file via SCP
4. Prompts for confirmation before restoring
5. Restores the database to local Docker container
6. Cleans up the downloaded file

Usage:
    ./fetch_prod_db.py --user USERNAME [--auto-confirm] [--keep-backup]
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init(autoreset=True)

# Configuration
REMOTE_HOST = "ssh.makerspace.se"
REMOTE_PATH = "/home/johank/docker/MakerAdmin/makeradmin"


def colored(text: str, color: str = "", bold: bool = False) -> str:
    """
    Apply color formatting to text using colorama.

    Args:
        text: The text to colorize
        color: Color name ('red', 'green', 'yellow', 'blue')
        bold: Whether to make the text bold

    Returns:
        Colored text with ANSI escape codes
    """
    color_map = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
    }

    result = ""
    if bold:
        result += Style.BRIGHT
    if color in color_map:
        result += color_map[color]
    result += text

    return result


def print_step(message: str):
    """Print a step in the process."""
    print(f"\n{colored(message, 'blue', bold=True)}")


def print_error(message: str):
    """Print an error message."""
    print(f"{colored('✗ Error: ' + message, 'red')}", file=sys.stderr)


def print_success(message: str):
    """Print a success message."""
    print(f"{colored('✓ ' + message, 'green')}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{colored('⚠ ' + message, 'yellow')}")


def check_docker_installed():
    """Verify that Docker is installed."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        print_error("Docker or docker compose not found. Is Docker installed?")
        return False
    except subprocess.CalledProcessError:
        print_error("Docker is installed but not responding correctly.")
        return False


def stop_all_services():
    """Stop all Docker Compose services."""
    print_step("Stopping all services...")
    try:
        result = subprocess.run(["docker", "compose", "down"], capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print_warning(f"Some services may not have stopped cleanly: {result.stderr}")
        else:
            print_success("All services stopped")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timed out stopping services after 60 seconds")
    except Exception as e:
        raise RuntimeError(f"Failed to stop services: {e}")


def start_database():
    """Start only the database container."""
    print_step("Starting database container...")
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "db2"], capture_output=True, text=True, check=True, timeout=120
        )

        # Wait for database to be ready
        print("  Waiting for database to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "exec",
                    "-T",
                    "db2",
                    "mysqladmin",
                    "ping",
                    "-h",
                    "localhost",
                    "-p${MYSQL_ROOT_PASSWORD}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print_success("Database is ready")
                return
            if attempt < max_attempts - 1:
                time.sleep(1)

        raise RuntimeError("Database did not become ready within 30 seconds")

    except subprocess.TimeoutExpired:
        raise RuntimeError("Timed out starting database")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to start database: {e.stderr}")


def stop_database():
    """Stop the database container."""
    print("Stopping database container...")
    try:
        subprocess.run(["docker", "compose", "stop", "db2"], capture_output=True, text=True, check=True, timeout=30)
        print_success("Database stopped")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timed out stopping database after 30 seconds")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to stop database: {e.stderr}")


def run_remote_backup(remote_user: str) -> str:
    """
    SSH to production server and create a database backup in /tmp.

    Args:
        remote_user: SSH username for the remote server

    Returns:
        Remote path to the backup file

    Raises:
        RuntimeError: If backup fails
    """
    print_step("Creating fresh backup on production server...")

    timestamp = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
    filename = f"db_{timestamp}.sql"
    remote_tmp_path = f"/tmp/{filename}"

    # Create the backup directly using docker commands, saving to /tmp on the host
    # This avoids permission issues with the data/db_backup directory
    # The redirect happens OUTSIDE docker exec, so the file goes to host /tmp
    backup_commands = (
        f"cd {REMOTE_PATH} && "
        f"docker compose exec -T db2 bash -c 'mysqldump -p${{MYSQL_ROOT_PASSWORD}} --create-options --complete-insert --quote-names makeradmin' > {remote_tmp_path}"
    )

    ssh_command = ["ssh", f"{remote_user}@{REMOTE_HOST}", backup_commands]

    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,  # 5 minute timeout for backup
        )

        # Check file size to verify backup succeeded
        size_check = subprocess.run(
            ["ssh", f"{remote_user}@{REMOTE_HOST}", f"stat -c%s {remote_tmp_path}"],
            capture_output=True,
            text=True,
            check=True,
        )

        size_bytes = int(size_check.stdout.strip())
        size_mb = size_bytes / (1024 * 1024)

        if size_bytes == 0:
            raise RuntimeError("Backup file is empty")

        print_success(f"Backup created: {filename} ({size_mb:.1f} MB)")
        return remote_tmp_path

    except subprocess.TimeoutExpired:
        raise RuntimeError("Backup timed out after 5 minutes")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else ""
        # Filter out mysqldump password warning
        stderr_filtered = "\n".join([line for line in stderr.split("\n") if "password on the command line" not in line])
        if stderr_filtered.strip():
            raise RuntimeError(f"Backup failed: {stderr_filtered}")
        raise RuntimeError(f"Backup failed with exit code {e.returncode}")


def download_backup(remote_path: str, dest_path: Path, remote_user: str) -> None:
    """
    Download backup file from production server using SCP.

    Args:
        remote_path: Full remote path to the backup file (e.g., '/tmp/db_2025-01-24T12_30_45.sql')
        dest_path: Local path where the file should be saved
        remote_user: SSH username for the remote server

    Raises:
        RuntimeError: If download fails
    """
    print_step("Downloading backup from production server...")

    remote_file = f"{remote_user}@{REMOTE_HOST}:{remote_path}"

    scp_command = ["scp", "-q", remote_file, str(dest_path)]

    try:
        subprocess.run(scp_command, check=True, timeout=600)  # 10 minute timeout

        file_size = dest_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        print_success(f"Downloaded {size_mb:.1f} MB to {dest_path}")

    except subprocess.TimeoutExpired:
        raise RuntimeError("Download timed out after 10 minutes")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Download failed: {e}")


def confirm_restore(auto_confirm: bool) -> bool:
    """
    Ask user to confirm database restoration.

    Args:
        auto_confirm: If True, skip confirmation and return True

    Returns:
        True if user confirmed, False otherwise
    """
    if auto_confirm:
        print_warning("Auto-confirm enabled, skipping confirmation prompt")
        return True

    print_step("Confirmation required")
    print(f"\n{colored('⚠  WARNING ⚠', 'red', bold=True)}")
    print(f"{colored('This will COMPLETELY REPLACE your local database!', 'red')}")
    print(f"{colored('All current local data will be LOST!', 'red')}\n")

    while True:
        try:
            response = input("Are you sure you want to continue? [yes/no]: ").strip().lower()
            if response in ("yes", "y"):
                return True
            elif response in ("no", "n"):
                print("Restoration cancelled.")
                return False
            else:
                print("Please answer 'yes' or 'no'.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nRestoration cancelled.")
            return False


def restore_database(dump_file: Path) -> None:
    """
    Restore database from dump file to local Docker container.

    Args:
        dump_file: Path to the SQL dump file

    Raises:
        RuntimeError: If restoration fails
    """
    print_step("Restoring database to local container...")

    # Import the restore function from db_restore.py
    # We do this here to avoid import issues if the module doesn't exist
    try:
        from db_restore import restore_database as db_restore_fn
    except ImportError:
        # Fallback: implement restore directly
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
                result = subprocess.run(cmd, stdin=sql_file, capture_output=True)
                if result.returncode != 0:
                    raise RuntimeError(f"Restore command failed: {result.stderr.decode()}")
        except Exception as e:
            raise RuntimeError(f"Restore failed: {e}")
    else:
        # Use the imported function
        if not db_restore_fn(str(dump_file)):
            raise RuntimeError("Database restoration failed")

    print_success("Database restored successfully!")


def cleanup_remote_backup(remote_path: str, remote_user: str):
    """
    Remove backup file from remote /tmp directory.

    Args:
        remote_path: Full remote path to the backup file
        remote_user: SSH username for the remote server
    """
    try:
        subprocess.run(
            ["ssh", f"{remote_user}@{REMOTE_HOST}", f"rm {remote_path}"], capture_output=True, check=True, timeout=10
        )
    except Exception as e:
        print_warning(f"Could not remove remote temp file: {e}")
        print(f"Please manually delete: {remote_user}@{REMOTE_HOST}:{remote_path}")


def cleanup_local_backup(dump_file: Path, keep_backup: bool):
    """
    Clean up downloaded backup file.

    Args:
        dump_file: Path to the backup file
        keep_backup: If True, keep the file; otherwise delete it
    """
    if keep_backup:
        print_step(f"Keeping backup file: {dump_file}")
        print_success(f"Backup saved at: {dump_file}")
    else:
        print_step("Cleaning up downloaded backup file...")
        try:
            dump_file.unlink()
            print_success("Cleanup complete")
        except Exception as e:
            print_warning(f"Could not delete backup file: {e}")
            print(f"Please manually delete: {dump_file}")


def cleanup_on_error(db_started: bool, temp_file: Path, remote_backup_path: str | None, remote_user: str):
    """
    Clean up resources after an error or interruption.

    Args:
        db_started: Whether the database was started
        temp_file: Path to the temporary backup file
        remote_backup_path: Path to the remote backup file, if created
        remote_user: SSH username for the remote server
    """
    if db_started:
        print("Stopping database...")
        try:
            stop_database()
        except Exception as e:
            print_warning(f"Could not stop database: {e}")

    if temp_file.exists():
        print(f"Cleaning up temporary file: {temp_file}")
        try:
            temp_file.unlink()
        except Exception as e:
            print_warning(f"Could not delete temp file: {e}")

    if remote_backup_path:
        print("Cleaning up remote backup file...")
        try:
            cleanup_remote_backup(remote_backup_path, remote_user)
        except Exception as e:
            print_warning(f"Could not clean up remote file: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch production database and restore it locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user aron                    # Interactive mode (recommended)
  %(prog)s --user aron --keep-backup      # Keep the downloaded backup file
  %(prog)s --user aron --auto-confirm     # Skip confirmation (dangerous!)

This script will:
  1. Stop all Docker services
  2. Start only the database container
  3. Create a fresh backup on the production server
  4. Download it via SCP
  5. Ask for confirmation (unless --auto-confirm)
  6. Restore to your local Docker database
  7. Stop the database container
  8. Clean up (unless --keep-backup)

Note: All services will be stopped after completion. Run 'make dev' to restart.
        """,
    )
    parser.add_argument("--user", required=True, help="SSH username for connecting to the production server")
    parser.add_argument("--auto-confirm", action="store_true", help="Skip confirmation prompt (use with caution!)")
    parser.add_argument(
        "--keep-backup", action="store_true", help="Keep the downloaded backup file instead of deleting it"
    )

    args = parser.parse_args()

    print(f"{colored('=== Fetch Production Database ===', bold=True)}\n")

    # Pre-flight checks
    print("Running pre-flight checks...")

    if not check_docker_installed():
        sys.exit(1)

    print_success("Docker is installed")

    # Temporary file for download
    temp_file = Path(f"prod_db_download_{os.getpid()}.sql")
    db_started = False
    remote_backup_path = None

    try:
        # Step 1: Stop all services
        stop_all_services()

        # Step 2: Start database only
        start_database()
        db_started = True

        # Step 3: Run backup on production
        remote_backup_path = run_remote_backup(args.user)

        # Step 4: Download backup
        download_backup(remote_backup_path, temp_file, args.user)

        # Step 5: Confirm restoration
        if not confirm_restore(args.auto_confirm):
            print("\nAborted. No changes were made to your local database.")
            cleanup_on_error(db_started, temp_file, remote_backup_path, args.user)
            sys.exit(0)

        # Step 6: Restore database
        restore_database(temp_file)

        # Step 7: Stop database
        print_step("Stopping database container...")
        stop_database()
        db_started = False

        # Step 8: Cleanup
        cleanup_local_backup(temp_file, args.keep_backup)

        # Clean up remote backup file from /tmp
        if remote_backup_path:
            print("Cleaning up remote backup file...")
            cleanup_remote_backup(remote_backup_path, args.user)

        print(f"\n{colored('✓ All done!', 'green', bold=True)}")
        print(f"{colored('Your local database now matches production.', 'green')}")
        print(f"\n{colored('Note: All services are stopped. Run `make dev` to start them.', 'yellow')}\n")

    except KeyboardInterrupt:
        print_error("\n\nInterrupted by user")
        cleanup_on_error(db_started, temp_file, remote_backup_path, args.user)
        sys.exit(130)

    except Exception as e:
        print_error(str(e))
        cleanup_on_error(db_started, temp_file, remote_backup_path, args.user)
        sys.exit(1)


if __name__ == "__main__":
    main()
