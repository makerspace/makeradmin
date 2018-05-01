import json
from logging import getLogger

from multi_access.models import User
from multi_access.util import dt_format, dt_cet


logger = getLogger("makeradmin")


def user_to_dict(user):
    try:
        member_number = int(user.name)
    except ValueError:
        logger.warning(f"can not convert {repr(user.name)} to int (row {user.id}), skipping")
        return None

    if user.stop_timestamp:
        end_timestamp = dt_format(dt_cet(user.stop_timestamp))
    else:
        end_timestamp = None
        
    return dict(
        member_number=member_number,
        rfid_tag=user.card,
        end_timestamp=end_timestamp,
    )


def export_to_json(session, customer_id):
    return json.dumps(
        [u for u in (user_to_dict(user) for user in session.query(User).filter_by(customer_id=customer_id)) if u],
        ensure_ascii=True,
        indent=2
    )
    
