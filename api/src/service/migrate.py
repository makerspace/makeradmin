import re
from collections import namedtuple
from contextlib import closing
from datetime import datetime

from sqlalchemy import inspect

from service.logging import logger
from os.path import join
from os import listdir


MigrationFile = namedtuple("MigrationFile", "date,name,file_path")
Migration = namedtuple("Migration", "id,service,date,name,file_path")


def read_sql(filename):
    with open(filename) as r:
        content = "\n".join(l for l in r if not l.startswith('--'))
        return (sql for sql in (s.strip() for s in content.split(';')) if sql)


def ensure_migrations_table(engine, session_factory):
    """ Create migrations table if not exists. """
    
    table_names = inspect(engine).get_table_names()
    if 'migrations' not in table_names:
        with closing(session_factory()) as session:
            session = session_factory()
            logger.info("creating migrations table")
            session.execute("ALTER DATABASE makeradmin CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci")
            session.execute("CREATE TABLE migrations ("
                            "    id INTEGER NOT NULL,"
                            "    service VARCHAR(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,"
                            "    name VARCHAR(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,"
                            "    applied_at DATETIME NOT NULL,"
                            "    PRIMARY KEY (service, id)"
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci")
            session.commit()


def get_service_migrations(service_name, migrations_dir):

    files = []
    for filename in listdir(migrations_dir):
        m = re.match(r'^((\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})_.*)\.sql', filename)

        if not m:
            logger.warning(f"{service_name}, {migrations_dir}/{filename} not matching file pattern, skipping")
            continue

        files.append(MigrationFile(m.group(2), m.group(1), join(migrations_dir, filename)))

    files.sort(key=lambda m: m.date)
    migrations = [Migration(i, service_name, f.date, f.name, f.file_path) for i, f in enumerate(files, start=1)]
    return migrations


def run_migrations(session_factory, migrations):
    
    with closing(session_factory()) as session:
        applied = {(i, s): n for i, s, n in
                   session.execute("SELECT id, service, name FROM migrations ORDER BY ID")}
        session.commit()
        
        logger.info(f"{len(migrations) - len(applied)} migrations to apply"
                    f", {len(applied)} migrations already applied")

        migrations.sort(key=lambda m: m.date)
        for migration in migrations:
            try:
                if (migration.id, migration.service) in applied:
                    if migration.name != applied[(migration.id, migration.service)]:
                        raise Exception(f"migrations name mismatch {migration.name}, "
                                        f"{applied[(migration.id, migration.service)]}")
                    continue
        
                logger.info(f"applying {migration.service}, {migration.name}")
        
                for sql in read_sql(migration.file_path):
                    session.execute(sql)
                    
                session.execute("INSERT INTO migrations VALUES (:id, :service, :name, :applied_at)",
                                {'id': migration.id, 'service': migration.service, 'name': migration.name,
                                 'applied_at': datetime.utcnow()})
                session.commit()
            except Exception:
                session.rollback()
                raise
