from service.internal_service import InternalService


service = InternalService(name='member', migrations=False)


import member.views
