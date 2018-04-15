import json

from destroyer.models import User
from test.util import dt_format, dt_cet


def user_to_dict(user):
    member_id = int(user.name)
    rfid_tag = user.card
    end_timestamp = dt_format(dt_cet(user.stop_timestamp))
    return dict(
        member_id=member_id,
        rfid_tag=rfid_tag,
        end_timestamp=end_timestamp,
    )


def export_to_json(session, customer_id):
    return json.dumps(
        [user_to_dict(user) for user in session.query(User).filter_by(customer_id=customer_id) if user],
        ensure_ascii=True,
        indent=2
    )
    
