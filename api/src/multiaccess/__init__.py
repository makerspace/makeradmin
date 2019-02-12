from service.internal_service import InternalService


service = InternalService(name='multiaccess', migrations=False)


import multiaccess.views
