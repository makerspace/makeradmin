

class InternalService:
    """ Flask blueprint for internal service that handles requests within the same process, authentication and
    permissions is handled by this class. """
    
    def __init__(self, config):
        self.config = config

