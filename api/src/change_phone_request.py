from datetime import timedelta, datetime
from random import randint
import logging

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from membership.models import PhoneNumberChangeRequest
from service.db import db_session
from service.error import NotFound, BadRequest

logger = logging.getLogger('makeradmin')


def change_phone_request(member_id, phone):
    logging.info(f'member {member_id} channge phone number request, phone {phone}')
    now = datetime.utcnow()

    total_requests = db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.timestamp >= now-timedelta(days=30)).count()
    if total_requests > 340:
        logging.info(f'member {member_id} channge phone number request, too many total requests ({total_requests}) last 30 days')
        raise BadRequest("Makerspace sms-quota är slut, prova igen om några dagar.")

    num_requests = db_session.query(PhoneNumberChangeRequest).filter(
        PhoneNumberChangeRequest.member_id == member_id, PhoneNumberChangeRequest.timestamp >= now-timedelta(days=30)
    ).count()
    if num_requests > 3:
        logging.info(f'member {member_id} channge phone number request, too many requests lately')
        raise BadRequest("För många ändringar av numret, testa igen om några veckor.")

    #TODO validate phone number
    #TODO change format of number?
    #TODO accessy and sms thing has same format?

    validation_code = f"{randint(0, 999_999):06d}"

    #TODO send validation code with sms

    change_request = PhoneNumberChangeRequest(member_id=member_id, phone=phone, validation_code=validation_code,
                                              completed=False, timestamp=datetime.utcnow())
    db_session.add(change_request)
    db_session.flush()
    logging.info(f'member {member_id} change phone number request, sms sent, phone {phone}, code {validation_code}')


def change_phone_validate(member_id, validation_code):
    logging.info(f'member {member_id} validating phone number, code {validation_code}')
    now = datetime.utcnow()
    
    try:
        change_request = db_session.query(PhoneNumberChangeRequest).filter(
            PhoneNumberChangeRequest.member_id == member_id,
        ).order_by(desc(PhoneNumberChangeRequest.timestamp)).first()
        if change_request.timestamp <= now-timedelta(minutes=5):
            logging.info(f'member {member_id} validating phone number, too old request, code {validation_code}')
            raise BadRequest("Koden är gammal")
        
        if change_request.validation_code == validation_code:
            change_request.member.phone = change_request.phone
            db_session.flush()
            logging.info(f'member {member_id} validating phone number, success, changed phone number to {change_request.phone}')
            return {}
    
    except NoResultFound:
        pass
    
    logging.info(f'member {member_id} validating phone number, no request for this member')
    raise NotFound("Koden är fel")
