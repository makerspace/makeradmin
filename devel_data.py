#!/usr/bin/env python3
import servicebase_python.service
import json
from pprint import pprint

gateway = servicebase_python.service.gateway_from_envfile(".env")

"labaccess"
"special_labaccess"
"membership"


def delete_all_spans(member_id):
    response = gateway.get("membership/span")
    print("list", response.status_code)
    spans = json.loads(response.content.decode())['data']
    for span in spans:
        response = gateway.delete(f"membership/span/{span['span_id']}")
        print("delete", response.status_code)
        

def create_span(member_id, startdate, enddate, span_type, creation_reason=None):
    payload = dict(
        member_id=member_id,
        startdate=startdate,
        enddate=enddate,
        span_type=span_type,
        creation_reason=creation_reason,
    )

    response = gateway.post("membership/span", payload=payload)
    print("create", response.status_code)
    pprint(json.loads(response.content.decode()))


member_id = 76
    
delete_all_spans(member_id)

create_span(member_id, "2016-05-20", "2016-06-21", "labaccess")
create_span(member_id, "2016-06-21", "2016-07-21", "labaccess")

create_span(member_id, "2018-05-10", "2018-07-10", "labaccess")
create_span(member_id, "2018-07-11", "2018-11-11", "labaccess")

create_span(member_id, "2018-05-20", "2019-05-20", "membership")

create_span(member_id, "2018-05-10", "2019-05-10", "special_labaccess")
