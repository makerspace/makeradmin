import re
from collections import namedtuple
from contextlib import closing
from datetime import datetime

from sqlalchemy import inspect

from service.logging import logger
from os.path import join
from os import listdir


Migration = namedtuple("Migration", "id,name")


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


def migrate_service(session_factory, service_name, migrations_dir):
    
    with closing(session_factory()) as session:
        logger.info(f"{service_name}, migrating")
    
        migrations = []
        for filename in listdir(migrations_dir):
            m = re.match(r'^((\d+)_.*)\.sql', filename)
    
            if not m:
                logger.warning(f"{service_name}, {migrations_dir}/{filename} not matching file pattern, skipping")
                continue
            
            migrations.append(Migration(int(m.group(2)), m.group(1)))
        
        migrations.sort(key=lambda m: m.id)
        
        applied = {i: Migration(i, n) for i, n in
                   session.execute("SELECT id, name FROM migrations WHERE service = :service ORDER BY ID",
                                   {'service': service_name})}
        session.commit()
        
        logger.info(f"{service_name}, {len(migrations) - len(applied)} migrations to apply"
                    f", {len(applied)} migrations already applied")
        
        for i, migration in enumerate(migrations, start=1):
            if i != migration.id:
                raise Exception(f"migrations should be numbered in sequence {migration.name} was not")
    
            if migration.id in applied:
                continue
    
            logger.info(f"{service_name}, applying {migration.name}")
    
            for sql in read_sql(join(migrations_dir, migration.name + '.sql')):
                session.execute(sql)
                
            session.execute("INSERT INTO migrations VALUES (:id, :service, :name, :applied_at)",
                            {'id': migration.id, 'service': service_name, 'name': migration.name,
                             'applied_at': datetime.utcnow()})
            session.commit()
