from service.internal_service import InternalService


service = InternalService(__name__, migrations=True)


import core.views
