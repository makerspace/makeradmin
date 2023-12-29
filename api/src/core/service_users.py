from dataclasses import dataclass
from typing import Sequence

from service.config import config
from service.api_definition import ALL_PERMISSIONS, MEMBER_VIEW, WEBSHOP, MEMBERBOOTH


@dataclass
class ServiceUser:
    id: int
    name: str
    permissions: Sequence[str] = ()
    token: str = None
    present: bool = True


TEST_SERVICE_USER_ID = -1
TEST_SERVICE_TOKEN = config.get("TEST_SERVICE_TOKEN")


SERVICE_USERS = (
    ServiceUser(
        id=TEST_SERVICE_USER_ID,
        name="test",
        permissions=ALL_PERMISSIONS,
        token=TEST_SERVICE_TOKEN,
        present=bool(TEST_SERVICE_TOKEN),
    ),
    ServiceUser(
        id=-2,
        name="memberbooth",
        permissions=[MEMBERBOOTH],
    ),
    ServiceUser(
        id=-3,
        name="multiaccess-program",
        permissions=[MEMBER_VIEW, WEBSHOP],
    ),
)


SERVICE_NAMES = {service_user.id: service_user.name for service_user in SERVICE_USERS}


SERVICE_PERMISSIONS = {service_user.id: service_user.permissions for service_user in SERVICE_USERS}
