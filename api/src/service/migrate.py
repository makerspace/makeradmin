import re
from collections import namedtuple
from importlib import import_module
from inspect import getfile
from datetime import datetime

from service.logging import logger
from importlib.util import module_from_spec
from importlib.util import spec_from_loader
from importlib.machinery import SourceFileLoader
from os.path import basename, splitext, dirname, join, exists
from os import listdir


def load_module_from_file(filename):
    module_name, _ = splitext(basename(filename))
    loader = SourceFileLoader(module_name, filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


Migration = namedtuple("Migration", "id,name")


def read_sql(filename):
    with open(filename) as r:
        content = "\n".join(l for l in r if not l.startswith('--'))
        return (sql for sql in (s.strip() for s in content.split(';')) if sql)


def migrate(session_factory, table_names, service_configs):
    session = session_factory()

    if 'migrations' not in table_names:
        logger.info("creating migrations table")
        session.execute("ALTER DATABASE makeradmin CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci");
        session.execute("CREATE TABLE migrations ("
                        "    id INTEGER NOT NULL,"
                        "    service VARCHAR(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,"
                        "    name VARCHAR(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,"
                        "    applied_at DATETIME NOT NULL,"
                        "    PRIMARY KEY (service, id)"
                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci")
        session.commit()
        
    for service_config in service_configs:
        # TODO Only for InternalServices and make it pythonic.
        
        logger.info(f"{service_config.name}, migrating")
    
        service_module = import_module(service_config.module)
        service_package_dir = dirname(getfile(service_module))
        migrations_dir = join(service_package_dir, 'migrations')
        if not exists(migrations_dir):
            logger.info(f"{service_config.name}, migrations dir {migrations_dir} does not exist, skipping service")
            continue
        
        migrations = []
        for filename in listdir(migrations_dir):
            m = re.match(r'^((\d+)_.*)\.sql', filename)

            if not m:
                logger.warning(f"{filename} not matching file pattern, skipping")
                continue
            
            migrations.append(Migration(int(m.group(2)), m.group(1)))
        
        migrations.sort(key=lambda m: m.id)
        
        applied = {i: Migration(i, n) for i, n in
                   session.execute("SELECT id, name FROM migrations WHERE service = :service ORDER BY ID",
                                   {'service': service_config.name})}
        session.commit()
        
        logger.info(f"{service_config.name}, {len(migrations) - len(applied)} migations to apply"
                    f", {len(applied)} migrations already applied")
        
        for i, migration in enumerate(migrations, start=1):
            if i != migration.id:
                raise Exception(f"migrations should be numbered in sequence {migration.name} was not")

            if migration.id in applied:
                continue

            logger.info(f"{service_config.name}, applying {migration.name}")

            for sql in read_sql(join(migrations_dir, migration.name + '.sql')):
                session.execute(sql)
                
            session.execute("INSERT INTO migrations VALUES (:id, :service, :name, :applied_at)",
                            {'id': migration.id, 'service': service_config.name, 'name': migration.name,
                             'applied_at': datetime.utcnow()})
            session.commit()

    logger.info("migrations complete")
    
    session.close()
    