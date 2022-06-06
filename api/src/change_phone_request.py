from dataclasses import asdict
from datetime import timedelta, datetime
from random import randint
import logging

from sqlalchemy.orm.exc import NoResultFound

from membership.models import Member, PhoneNumberChangeRequest
from service.db import db_session
from service.error import NotFound, BadRequest

logger = logging.getLogger('makeradmin') #TODO is it needed?

#TODO logging


def change_phone_request(member_id, phone):
    return {"kaka": "baja"}
    logging.info('asdf')
    now = datetime.utcnow()

    #TODO spam checks

    num_requests=db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == g.user_id, 
                                PhoneNumberChangeRequest.timestamp-timedelta(months=1) <= now).count()
    if num_requests > 3:
        logging.warning('asdf')
        raise BadRequest("Över maximala antalet ändrngar av telefonnummret per månad.")

    #TODO validate phone number
    #TODO change format of number?
    #TODO accessy and sms thing has same format?

    validation_code = f"{randint(1e6):06d}"

    #TODO send validation code with sms

    change_request = PhoneNumberChangeRequest(member_id=member_id, phone=phone, validation_code=validation_code,
                                              completed=False, timestamp=datetime.utcnow())
    db_session.add(change_request)
    db_session.flush()

    #TODO return errors

    return {"kaka": "baja"}


def change_phone_validate(member_id, validation_code):
    return {"kaka": "baja"}
    logging.info('asdf')
    now = datetime.utcnow()

    try:
        change_request = db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == member_id).one()
        if PhoneNumberChangeRequest.timestamp <= now-timedelta(minutes=5):
            logging.info('asdf')
            raise BadRequest("Ändringsförfrågan är för gammal")
        else:
            if change_request.validation_code == validation_code:
                setattr(change_request.member, phone)
                db_session.flush()
                logging.info('asdf')
            else:
                logging.info('asdf')
                raise BadRequest("Felaktig valideringskod")
    except NoResultFound:
        logging.info('asdf')
        raise NotFound("Finns ingen ändringsförfrågan")

    return {"kaka": "baja"}