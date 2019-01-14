from service.internal_service import InternalService


service = InternalService(name='membership', migrations=True)


import membership.views
