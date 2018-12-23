import re
from collections import namedtuple
from importlib import import_module
from inspect import getfile
from datetime import datetime

from component.logging import logger
from importlib.util import module_from_spec
from importlib.util import spec_from_loader
from importlib.machinery import SourceFileLoader
from os.path import basename, splitext, dirname, join, isdir, exists
from os import listdir


def load_module_from_file(filename):
    module_name, _ = splitext(basename(filename))
    loader = SourceFileLoader(module_name, filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


Migration = namedtuple("Migration", "id,name")


def migrate(session_factory, table_names, component_configs):
    session = session_factory()

    if 'migrations' not in table_names:
        logger.info("creating migrations table")
        session.execute("CREATE TABLE migrations ("
                        "    id INTEGER NOT NULL,"
                        "    component VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,"
                        "    name VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,"
                        "    applied_at DATETIME NOT NULL,"
                        "    PRIMARY KEY (id)"
                        ")")
        session.commit()
        
    for component_config in component_configs:
        logger.info(f"migrating {component_config.name}")
    
        component_module = import_module(component_config.module)
        component_package_dir = dirname(getfile(component_module))
        migrations_dir = join(component_package_dir, 'migrations')
        if not exists(migrations_dir):
            logger.info(f"migrations dir {migrations_dir} does not exist, skipping component")
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
                   session.execute("SELECT id, name FROM migrations WHERE component = :component ORDER BY ID",
                                   {'component': component_config.name})}
        session.commit()
        
        logger.info(f"{len(migrations) - len(applied)} migations to apply, {len(applied)} migrations already applied")
        
        for i, migration in enumerate(migrations, start=1):
            if i != migration.id:
                raise Exception(f"migrations should be numbered in sequence {migration.name} was not")

            if migration.id in applied:
                continue

            migration_sql = "INSERT INTO migrations VALUES (:id, :component, :name, :applied_at)"
            migration_args = {'id': migration.id, 'component': component_config.name, 'name': migration.name,
                              'applied_at': datetime.utcnow()}

            # TODO Make migrations with IF EXISTS robout instead, we still want to drop old tables.
            if migration.id == 1 and component_config.legacy_table in table_names:
                logger.info(f"skipping {migration.name}, legacy table already present")
                session.execute(migration_sql, migration_args)
                session.commit()
            else:
                logger.info(f"applying {migration.name}")
                with open(join(migrations_dir, migration.name + '.sql')) as r:
                    lines = "\n".join(l for l in r if not l.startswith('--'))
                    for sql in lines.split(';'):
                        session.execute(sql)
                session.commit()

    logger.info("migration complete")
    
    session.close()
    