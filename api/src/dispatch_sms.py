from logging import getLogger

import requests
from service.config import get_46elks_auth
from service.error import InternalServerError

logger = getLogger("makeradmin")


class NoAuthConfigured(Exception):
    pass


def send_sms(phone: str, message: str) -> requests.Response:
    data = {"from": "Makerspace", "to": phone, "message": message}
    auth = get_46elks_auth()
    if not auth:
        logger.info(f"NOT sending SMS, authentication not configured {phone=} {data=}")
        raise NoAuthConfigured("Cannot send SMS because the server has not been configured for it.")

    logger.info(f"sending sms {phone=} {data=}")

    return requests.post("https://api.46elks.com/a1/sms", auth=auth, data=data)


def send_validation_code(phone: str, validation_code: int) -> None:
    r = send_sms(phone, f"Kod: {validation_code}")
    if not r.ok:
        raise InternalServerError(f"kunde inte skicka sms", log=f"failed to send sms {phone=} {r=}")
