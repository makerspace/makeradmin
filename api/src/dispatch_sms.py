from datetime import datetime, timedelta

from membership.models import Member, normalise_phone_number
from membership.models import PhoneNumberChangeRequest

def send_sms(phone, message):
    try:
        phone = normalise_phone_number(phone)
    except ValueError as e:
        raise BadRequest("Dåligt formatterat telefonnummer.")
    
    #TODO

def send_validation_code(phone, validation_code):
    print("TODO")