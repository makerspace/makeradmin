"""Storage module for generic file and image storage."""

from service.internal_service import InternalService

service = InternalService(name="storage")

import storage.views
