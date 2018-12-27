

class ExternalService:
    """ Flask blueprint for external services that sends all requests to an external service. Authentication is done
    here and permission information is forwarded as HTTP headers. """
    
    def __init__(self, name, url):
        self.name = name
        self.url = url
        
    def migrate(self, *args, **kwargs):
        pass

