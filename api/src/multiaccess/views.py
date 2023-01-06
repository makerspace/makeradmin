from flask import g
from sqlalchemy.orm import contains_eager

from membership.models import Member, Span, Key
from multiaccess import service
from multiaccess.box_terminator import box_terminator_validate, box_terminator_nag, \
    box_terminator_boxes
from service.api_definition import GET, Arg, MEMBER_EDIT, POST, MEMBER_VIEW, symbol, MEMBERBOOTH
from service.db import db_session
from service.logging import logger
from .util import member_to_response_object
from .memberbooth import pin_login_to_memberinfo, tag_to_memberinfo, member_number_to_memberinfo


@service.route("/memberdata", method=GET, permission=MEMBER_VIEW)
def get_memberdata():
    """ Used by multiaccess program to get members. """
    query = db_session.query(Member).join(Member.spans).join(Member.keys)
    query = query.options(contains_eager(Member.spans), contains_eager(Member.keys))
    query = query.filter(
        Member.deleted_at.is_(None),
        Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
        Span.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    return [member_to_response_object(m) for m in query]


@service.route("/memberbooth/tag", method=GET, permission=MEMBERBOOTH)
def memberbooth_tag(tagid=Arg(int)):
    return tag_to_memberinfo(tagid)


@service.route("/memberbooth/pin-login", method=GET, permission=MEMBERBOOTH)
def memberbooth_pin_login(member_id=Arg(int), pin_code=Arg(str)):
    return pin_login_to_memberinfo(member_id, pin_code)


@service.route("/memberbooth/member", method=GET, permission=MEMBERBOOTH)
def memberbooth_member(member_number=Arg(int)):
    return member_number_to_memberinfo


@service.route("/box-terminator/boxes", method=GET, permission=MEMBER_EDIT)
def box_terminator_boxes_routes():
    """ Returns a list of all boxes scanned, ever. """
    return box_terminator_boxes()


@service.route("/box-terminator/nag", method=POST, permission=MEMBER_EDIT)
def box_terminator_nag_route(member_number=Arg(int), box_label_id=Arg(int), nag_type=Arg(symbol)):
    """ Send a nag email for this box. """
    return box_terminator_nag(member_number, box_label_id, nag_type)


@service.route("/box-terminator/validate-box", method=POST, permission=MEMBER_EDIT)
def box_terminator_validate_route(member_number=Arg(int), box_label_id=Arg(int)):
    """ Used when scanning boxes. """
    return box_terminator_validate(member_number, box_label_id, g.session_token)
