from quiz.views import member_quiz_statistics
from flask import request, g

from member import service
from member.member import send_access_token_email
from membership.member_auth import get_member_permissions
from membership.membership import get_membership_summary
from membership.views import member_entity
from service.api_definition import POST, PUBLIC, Arg, GET, USER


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str, required=False), user_identification: str=Arg(str)):
    """ Send access token email to user with username or member_number user_identification. """
    return send_access_token_email(redirect or "/member", user_identification, request.remote_addr,
                                   request.user_agent.string)


@service.route("/current", method=GET, permission=USER)
def current_member():
    """ Get current member. """
    return member_entity.read(g.user_id)


@service.route("/current/permissions", method=GET, permission=USER)
def current_permissions():
    """ Get current member permissions. """
    return {"permissions": [p for _, p in get_member_permissions(g.user_id)]}


@service.route("/current/membership", method=GET, permission=USER)
def current_membership_info():
    """ Get current user membership information. """
    return get_membership_summary(g.user_id).as_json()


@service.route("/current/quizzes", method=GET, permission=USER)
def current_member_quiz_info():
    """ Get info about which quizzes the current user has completed. """
    return member_quiz_statistics(g.user_id)
