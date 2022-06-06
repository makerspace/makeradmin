from datetime import timedelta, datetime
from random import randint
import logging

from sqlalchemy.orm.exc import NoResultFound, update

from membership.models import Member, PhoneNumberChangeRequest
from service.db import db_session
from service.error import NotFound, BadRequest

logger = logging.getLogger('makeradmin') #TODO is it needed?

#TODO logging

def change_phone_request(member_id, phone):
    logging.info('asdf')
    now = datetime.utcnow()

    #TODO spam checks

    #TODO limit number of phone number changes per member per month
    db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == g.user_id, 
                                                    PhoneNumberChangeRequest.timestamp-timedelta(minutes=5) <= now).one()

    #TODO validate phone number
    #TODO change format of number?
    #TODO accessy and sms thing has same format?

    validation_code = randint(1e5, 1e6-1)

    #TODO send validation code with sms

    change_request = PhoneNumberChangeRequest(member_id=member_id, phone=phone, validation_code=validation_code,
                                            completed=False, timestamp=datetime.utcnow())
    db_session.add(change_request)
    db_session.flush()

    #TODO return errors

    return {}

def change_phone_validate(member_id, phone, validation_code):
    logging.info('asdf')
    now = datetime.utcnow()

    try:
        change_request = db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == member_id,
                                           PhoneNumberChangeRequest.timestamp-timedelta(minutes=5) <= now).one()
        if change_request.validation_code == validation_code:
            setattr(change_request.member, phone)
            db_session.flush()
        else:
            logging.warning('asdf')
            raise BadRequest("Incorrect validation code")
    except NoResultFound:
        logging.warning('asdf')
        raise NotFound("Missing request or old request")

    return {}
