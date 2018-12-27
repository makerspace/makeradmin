from inspect import getmodule, stack, getfile
from os.path import dirname, join, isdir, exists

from flask import Blueprint
from service.migrate import migrate_service


class InternalService(Blueprint):
    """ Flask blueprint for internal service that handles requests within the same process, authentication and
    permissions is handled by this class. """
    
    def __init__(self, name, migrations=True):
        """
        The name of the service, this should be __name__.
        
        :param migrations set to True if there is a migrations dir with migrations in this service
        """
        
        super().__init__(name, name)
        self.migrations = migrations
        self.service_module = getmodule(stack()[1][0])

    def migrate(self, session_factory):
        if self.migrations:
            service_package_dir = dirname(getfile(self.service_module))
            migrations_dir = join(service_package_dir, 'migrations')
            
            if not exists(migrations_dir) and not isdir(migrations_dir):
                raise Exception(f"service {self.name} migrations dir {migrations_dir} is missing")
            
            migrate_service(session_factory, self.name, migrations_dir)
