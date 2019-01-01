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

"""
insert into membership_group_permissions (id, group_id,
permission_id) values ( 1, 1, 1), ( 2, 1, 2),( 3, 1, 3), ( 4, 1, 4),
( 5, 1, 5), ( 6, 1, 6), ( 7, 1, 7), ( 8, 1, 8), ( 9, 1, 9), (10, 1,
10), (11, 1, 11), (12, 1, 12), (13, 1, 13), (14, 1, 14), (15, 1,
15), (16, 1, 16), (17, 1, 17), (18, 1, 18), (19, 1, 19), (20, 1,
20);
"""


"""
date -u +%s
curl -X PUT http://localhost:8010/webshop/process_stripe_events -d '{"source_id": "src_1Dgf3ELA7yYBn2H1gHYkdBNe", "start": null}' -H "Content-Type: application/json"  -H 'Authorization: Bearer f1671e0cfdb61d4cd7b280e72173e385' -v
SET FOREIGN_KEY_CHECKS = 0; DROP TABLE IF EXISTS `access_tokens`; DROP TABLE IF EXISTS `login`; DROP TABLE IF EXISTS `membership_group_permissions`; DROP TABLE IF EXISTS `membership_groups`; DROP TABLE IF EXISTS `membership_keys`; DROP TABLE IF EXISTS `membership_members`; DROP TABLE IF EXISTS `membership_members_groups`; DROP TABLE IF EXISTS `membership_members_roles`; DROP TABLE IF EXISTS `membership_permissions`; DROP TABLE IF EXISTS `membership_roles`; DROP TABLE IF EXISTS `membership_spans`; DROP TABLE IF EXISTS `messages_message`; DROP TABLE IF EXISTS `messages_recipient`; DROP TABLE IF EXISTS `messages_template`; DROP TABLE IF EXISTS `migrations`; DROP TABLE IF EXISTS `relations`; DROP TABLE IF EXISTS `services`; DROP TABLE IF EXISTS `webshop_actions`; DROP TABLE IF EXISTS `webshop_pending_registrations`; DROP TABLE IF EXISTS `webshop_product_actions`; DROP TABLE IF EXISTS `webshop_product_categories`; DROP TABLE IF EXISTS `webshop_product_images`; DROP TABLE IF EXISTS `webshop_product_variants`; DROP TABLE IF EXISTS `webshop_products`; DROP TABLE IF EXISTS `webshop_stripe_pending`; DROP TABLE IF EXISTS `webshop_transaction_actions`; DROP TABLE IF EXISTS `webshop_transaction_contents`; DROP TABLE IF EXISTS `webshop_transactions`; DROP TABLE IF EXISTS `services`; DROP TABLE IF EXISTS `relations`;  DROP TABLE IF EXISTS `migrations_webshop`;  DROP TABLE IF EXISTS `migrations_membership`;   DROP TABLE IF EXISTS `migrations_messages`;  SET FOREIGN_KEY_CHECKS = 1;

"""
