from service.config import config
from service.internal_service import InternalService

service = InternalService(name="/webshop/accounting")

# This import is needed to register the routes
import shop.accounting.views
