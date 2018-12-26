

class ExternalService:
    """ Flask view for external services that sends all requests to an external service. Authentication is done here
    and permission informations is forwarded as HTTP headers. """
    
    def __init__(self, config):
        self.config = config

