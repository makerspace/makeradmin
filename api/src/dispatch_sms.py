from logging import getLogger

import requests

from service.config import get_46elks_auth
from service.error import InternalServerError, UnprocessableEntity

logger = getLogger("makeradmin")


def send_sms(phone: str, message: str) -> None:
    data = {"from": "Makerspace", "to": phone, "message": message}
    auth = get_46elks_auth()
    if not auth:
        logger.info(f"NOT sending sms, no auth configured {phone=} {data=}")
        raise UnprocessableEntity("Cannot send SMS because the server has not been configured for it.")

    logger.info(f"sending sms {phone=} {data=}")

    response = requests.post("https://api.46elks.com/a1/sms", auth=auth, data=data)
    if not response.ok:
        raise InternalServerError(f"kunde inte skicka sms", log=f"failed to send sms {phone=} {data=} {response=}")


def send_validation_code(phone: str, validation_code: int) -> None:
    send_sms(phone, f"Kod: {validation_code}")
