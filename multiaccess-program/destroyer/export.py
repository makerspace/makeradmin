import json

from sqlalchemy import text

from destroyer.models import User


def export_to_json(Session, customer_id=16):
    session = Session()
    return json.dumps([dict(
        member_id=user.name,
        rfid_tag=None,
        end_timestamp=str(user.stop_timestamp),
        changed=user.changed,
    )
        for user in session.query(User).filter_by(customer_id=16)],
        ensure_ascii=True,
        indent=2)
