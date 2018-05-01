

# TODO Complete this when we have decided on login.
class MakerAdminSimpleTokenAuth(object):
    
    def __init__(self, access_token=None, token_filename=None):
        self.token = access_token
    
    def get_headers(self):
        """ Get headers needed for login. """
        return dict(token=self.token)
    


