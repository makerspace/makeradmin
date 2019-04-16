from service.internal_service import InternalService


service = InternalService(name='statistics', migrations=False)


import statistics.views
