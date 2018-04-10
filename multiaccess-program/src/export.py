import json

from sqlalchemy import text


def export_to_json(db, customer_id=16):
    with db.connect() as conn:
        res = conn.execute(text("SELECT Name, Card, Stop FROM Users WHERE customerId = :customer_id"),
                           customer_id=customer_id)
        return json.dumps([{'member_id': int(row['Name']), 'rfid_tag': int(row['Card']), 'end_timestamp': row['Stop']}
                           for row in res.fetchall()],
                          ensure_ascii=True,
                          indent=2)
    
