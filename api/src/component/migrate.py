import re
from collections import namedtuple
from importlib import import_module
from inspect import getfile
from datetime import datetime
from component.logging import logger
from importlib.util import module_from_spec
from importlib.util import spec_from_loader
from importlib.machinery import SourceFileLoader
from os.path import basename, splitext, dirname, join
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
    
        migrations_module = import_module(component_config.module + ".migrations")
        migrations_package_dir = dirname(getfile(migrations_module))
        
        migrations = []
        for filename in listdir(migrations_package_dir):
            m = re.match(r'^((\d+)_.*)\.py$', filename)

            if filename == '__init__.py':
                continue
            if not m:
                logger.warning(f"{filename} not matching file pattern, skipping")
                continue
            
            migrations.append(Migration(int(m.group(2)), m.group(1)))
        
        migrations.sort(key=lambda m: m.id)
        
        applied = {i: Migration(i, n) for i, n in
                   session.execute("SELECT id, name FROM migrations WHERE component = :component ORDER BY ID",
                                   {'component': component_config.name})}
        session.commit()
        
        for i, migration in enumerate(migrations, start=1):
            if i != migration.id:
                raise Exception(f"migrations should be numbered in sequence {migration.name} was not")

            if migration.id in applied:
                continue
                
            if migration.id == 1 and component_config.legacy_table in table_names:
                logger.info(f"skipping {migration.name}, legacy table already present")
                session.execute("INSERT INTO migrations VALUES (:id, :component, :name, :applied_at)",
                                {'id': migration.id, 'component': component_config.name, 'name': migration.name,
                                 'applied_at': datetime.utcnow()})
                session.commit()
            else:
                logger.info(f"applying {migration.name}")
                module = load_module_from_file(join(migrations_package_dir, migration.name + '.py'))
                getattr(module, 'run')(session)
                if not session.dirty:
                    raise Exception("session not dirty, you should not commit in migration, resolve this manually")
                session.commit()

    logger.info("migration complete")
    
    session.close()
    