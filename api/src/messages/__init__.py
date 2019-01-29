from service.internal_service import InternalService


service = InternalService(name='messages', migrations=True)


import messages.views
