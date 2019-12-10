from dataclasses import dataclass
from typing import Sequence

from service import config
from service.api_definition import ALL_PERMISSIONS, KEYS_VIEW, MEMBER_VIEW, WEBSHOP


@dataclass
class ServiceUser:
    id: int
    name: str
    permissions: Sequence[str] = ()
    token: str = None


SERVICE_USERS = (
    ServiceUser(id=-1, name="test", permissions=ALL_PERMISSIONS, token=config.get('API_BEARER', log_value=False)),
    ServiceUser(id=-2, name="memberbooth", permissions=[KEYS_VIEW, MEMBER_VIEW]),
    ServiceUser(id=-3, name="multiaccess-program", permissions=[MEMBER_VIEW, WEBSHOP]),
)