import re
from collections import namedtuple
from contextlib import closing
from datetime import datetime, timezone
from inspect import getfile, getmodule, stack
from os import listdir
from os.path import dirname, exists, isdir, join

from service.logging import logger
from sqlalchemy import inspect

Migration = namedtuple("Migration", "id,name")


def read_sql(filename):
    with open(filename) as r:
        content = "\n".join(l for l in r if not l.startswith("--"))
        return (sql for sql in (s.strip() for s in content.split(";")) if sql)


def ensure_migrations_table(engine, session_factory):
    """Create migrations table if not exists."""

    engine_inspect = inspect(engine)
    table_names = engine_inspect.get_table_names()
    if "migrations" not in table_names:
        with closing(session_factory()) as session:
            logger.info("creating migrations table")
            session.execute("ALTER DATABASE makeradmin CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci")
            session.execute(
                "CREATE TABLE migrations ("
                "    id INTEGER NOT NULL,"
                "    name VARCHAR(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,"
                "    applied_at DATETIME NOT NULL,"
                "    PRIMARY KEY (id)"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
            )
            session.commit()
    elif "service" in {c["name"] for c in engine_inspect.get_columns("migrations")}:
        with closing(session_factory()) as session:
            logger.info("updating existing migrations table")
            session.execute(
                "UPDATE migrations SET id=1, name='0001_initial_core'"
                "     WHERE id=1 AND service='core' AND name='0001_initial'"
            )
            session.execute(
                "UPDATE migrations SET id=5, name='0005_remove_excessive_permissions'"
                "    WHERE id=2 AND service='membership' AND name='0002_remove_excessive_permissions'"
            )
            session.execute(
                "UPDATE migrations SET id=6, name='0006_add_box'"
                "    WHERE id=3 AND service='membership' AND name='0003_add_box'"
            )
            session.execute(
                "UPDATE migrations SET id=2, name='0002_initial_membership'"
                "    WHERE id=1 AND service='membership' AND name='0001_initial'"
            )
            session.execute(
                "UPDATE migrations SET id=4, name='0004_initial_messages'"
                "    WHERE id=1 AND service='messages' AND name='0001_initial'"
            )
            session.execute(
                "UPDATE migrations SET id=7, name='0007_rename_everything'"
                "    WHERE id=2 AND service='messages' AND name='0002_rename_everything'"
            )
            session.execute(
                "UPDATE migrations SET id=3, name='0003_initial_shop'"
                "    WHERE id=1 AND service='shop' AND name='0001_initial'"
            )
            session.execute(
                "UPDATE migrations SET id=8, name='0008_password_reset_token'"
                "    WHERE id=2 AND service='core' AND name='0002_password_reset_token'"
            )
            session.execute("ALTER TABLE migrations DROP PRIMARY KEY, ADD PRIMARY KEY(id)")
            session.execute("ALTER TABLE migrations DROP COLUMN service")
            session.commit()


def run_migrations(session_factory):
    current_module = getmodule(stack()[1][0])
    source_dir = dirname(getfile(current_module))
    migrations_dir = join(source_dir, "migrations")

    if not exists(migrations_dir) and not isdir(migrations_dir):
        raise Exception(f"migrations dir {migrations_dir} is missing")

    with closing(session_factory()) as session:
        logger.info(f"running migrations")

        migrations = []
        for filename in listdir(migrations_dir):
            m = re.match(r"^((\d+)_.*)\.sql", filename)

            if not m:
                logger.warning(f"migrations, {migrations_dir}/{filename} not matching file pattern, skipping")
                continue

            migrations.append(Migration(int(m.group(2)), m.group(1)))

        migrations.sort(key=lambda m: m.id)

        applied = {i: Migration(i, n) for i, n in session.execute("SELECT id, name FROM migrations ORDER BY ID")}
        session.commit()

        logger.info(f"{len(migrations) - len(applied)} migrations to apply, {len(applied)} migrations already applied")

        for i, migration in enumerate(migrations, start=1):
            try:
                if i != migration.id:
                    raise Exception(f"migrations should be numbered in sequence {migration.name} was not")

                if migration.id in applied:
                    continue

                logger.info(f"migrations, applying {migration.name}")

                for sql in read_sql(join(migrations_dir, migration.name + ".sql")):
                    session.execute(sql)

                session.execute(
                    "INSERT INTO migrations VALUES (:id, :name, :applied_at)",
                    {"id": migration.id, "name": migration.name, "applied_at": datetime.now(timezone.utc)},
                )
                session.commit()
            except Exception:
                session.rollback()
                raise
