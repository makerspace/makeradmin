import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from random import randint

from dispatch_sms import NoAuthConfigured, send_validation_code
from membership.models import PhoneNumberChangeRequest, normalise_phone_number
from multiaccessy.invite import AccessyError, ensure_accessy_labaccess
from service.db import db_session
from service.error import BadRequest, NotFound, Unauthorized
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger("makeradmin")


def change_phone_request(member_id: int | None, phone: str) -> int:
    now = datetime.now(timezone.utc)

    try:
        phone = normalise_phone_number(phone)
        # Ensure that the number is still valid. Sometimes after normalization, it validates correctly, but is not actually valid.
        # This happens for example for the number "000".
        phone = normalise_phone_number(phone)
    except ValueError:
        raise BadRequest("Inte ett giltigt telefonnummer.")

    if member_id is not None:
        # Limit total number of requests in a month
        total_requests = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.timestamp >= now - timedelta(days=30))
            .count()
        )
        if total_requests > 1024:
            logging.info(
                f"member id {member_id} change phone number request, too many total requests ({total_requests}) last 30 days"
            )
            raise BadRequest("Makerspace sms-quota är slut, prova igen om några dagar.")

        # Limit tries for a member in a month
        member_requests = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(
                PhoneNumberChangeRequest.member_id == member_id,
                PhoneNumberChangeRequest.timestamp >= now - timedelta(days=30),
            )
            .count()
        )
        if member_requests > 10:
            logging.info(f"member id {member_id} change phone number request, too many requests lately")
            raise BadRequest("För många ändringsförsök, testa igen om några veckor.")

        # Limit changes for a member in a month
        success_requests = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(
                PhoneNumberChangeRequest.member_id == member_id,
                PhoneNumberChangeRequest.completed,
                PhoneNumberChangeRequest.timestamp >= now - timedelta(days=30),
            )
            .count()
        )
        if success_requests > 1:
            logging.info(f"member id {member_id} change phone number request, too many changes lately")
            raise BadRequest("För många ändringar av numret, testa igen om några veckor.")
    else:
        # Limit total number of requests in a day for non-authorized requests. Just to make sure we don't get spammed.
        total_requests = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.timestamp >= now - timedelta(days=1))
            .count()
        )
        if total_requests > 30:
            logging.info(f"change phone number request, too many total requests ({total_requests}) during last day")
            raise BadRequest("Makerspace sms-quota är slut, prova igen imorgon.")

    validation_code = randint(0, 999_999)

    try:
        send_validation_code(phone, validation_code)
        logging.info(
            f"member id {member_id} change phone number request, sms sent, phone {phone}, code {validation_code}"
        )
    except NoAuthConfigured:
        pass
    except Exception:
        raise BadRequest("Misslyckades med att skicka sms med verifikations kod")

    change_request = PhoneNumberChangeRequest(
        member_id=member_id,
        phone=phone,
        validation_code=validation_code,
        completed=False,
        timestamp=datetime.now(timezone.utc),
    )

    db_session.add(change_request)
    db_session.flush()

    request_count = (
        db_session.query(PhoneNumberChangeRequest)
        .filter(PhoneNumberChangeRequest.member_id == member_id, PhoneNumberChangeRequest.phone == phone)
        .count()
    )
    return change_request.id


def change_phone_validate(member_id: int | None, request_id: int, validation_code: str):
    logging.info(f"member {member_id} validating phone number, code {validation_code}")
    now = datetime.now(timezone.utc)

    try:
        change_request = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(
                PhoneNumberChangeRequest.id == request_id,
            )
            .order_by(desc(PhoneNumberChangeRequest.timestamp))
            .first()
        )

        if change_request.member_id is not None and member_id != change_request.member_id:
            raise Unauthorized("You can only change your own phone number.")

        if inc_tries(change_request.id) > 1000:
            logging.info(f"member id {member_id} validating phone number, too many tries, aborting")
            raise BadRequest("Du har gissat för många gånger")

        if change_request.completed:
            logging.info(
                f"member id {member_id} validating phone number, code already completed, code {validation_code}"
            )
            raise BadRequest("Koden är redan använd")

        if change_request.validation_code == validation_code and change_request.timestamp <= now - timedelta(minutes=8):
            logging.info(f"member id {member_id} validating phone number, too old request, code {validation_code}")
            raise BadRequest("Koden är för gammal")

        if change_request.validation_code == validation_code:
            change_request.completed = True
            if change_request.member_id is not None:
                change_request.member.phone = change_request.phone
                db_session.flush()
                logging.info(
                    f"member id {member_id} validating phone number, success, changed phone number to {change_request.phone}"
                )

                try:
                    ensure_accessy_labaccess(member_id)
                except AccessyError as e:
                    logger.warning(
                        f"failed to ensure accessy labacess after changing phone number, skipping, member (id {member_id}), member can self service add later: {e}"
                    )

            return {}

    except NoResultFound:
        pass

    logging.info(f"member id {member_id} validating phone number, no request for this member")
    raise NotFound("Felaktig kod")


validation_tries = defaultdict(lambda: 0)


def inc_tries(key: int) -> int:
    validation_tries[key] += 1
    return validation_tries[key]
