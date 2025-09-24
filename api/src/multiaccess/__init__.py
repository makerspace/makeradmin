from service.internal_service import InternalService

service = InternalService(name="multiaccess")

# Used to create short URLs for QR codes in labels
short_url_service = InternalService(name="L")

import multiaccess.views
