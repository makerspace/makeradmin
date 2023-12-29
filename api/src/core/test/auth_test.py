from flask import g

import core
import membership

from core import models
from core.auth import authenticate_request
from core.models import AccessToken
from core.service_users import TEST_SERVICE_USER_ID
from service.api_definition import USER, GET, PUBLIC, ALL_PERMISSIONS
from service.db import db_session
from service.error import Unauthorized, Forbidden
from test_aid.test_base import FlaskTestBase


class Test(FlaskTestBase):
    models = [core.models, membership.models]

    def test_user_id_and_permission_is_set_even_if_there_is_no_auth_header(self) -> None:
        with self.app.test_request_context():
            self.assertFalse(hasattr(g, "user_id"))
            self.assertFalse(hasattr(g, "permissions"))

            authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_no_auth_header_sets_correct_user_and_permissions(self) -> None:
        with self.app.test_request_context():
            authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_empty_auth_or_bad_header_raises_unauthorized(self) -> None:
        with self.app.test_request_context(headers=dict(Authorization="")):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

        with self.app.test_request_context(headers=dict(Authorization="dkopwkdw")):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_non_existing_access_token_raises_unauthorized(self) -> None:
        self.db.create_access_token(user_id=1)

        with self.app.test_request_context(headers=dict(Authorization="Bearer non-existent-token")):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_expired_token_raises_unautorized_and_removes_all_expired_tokens(self) -> None:
        self.db.create_access_token(user_id=1, access_token="expired-1", expires=self.datetime(days=-1))
        self.db.create_access_token(user_id=2, access_token="expired-2", expires=self.datetime(days=-1))
        self.db.create_access_token(user_id=3, access_token="not-expired-1", expires=self.datetime(days=1))

        with self.app.test_request_context(headers=dict(Authorization="Bearer expired-1")):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

        (access_token,) = db_session.query(AccessToken).all()

        self.assertEqual("not-expired-1", access_token.access_token)

    def test_valid_user_auth_updates_access_token_and_sets_user_id_and_permission(self) -> None:
        permission = self.db.create_permission()
        member = self.db.create_member()
        group = self.db.create_group()
        group.members.append(member)
        group.permissions.append(permission)

        access_token = self.db.create_access_token(user_id=member.member_id, expires=self.datetime(days=1))

        with self.app.test_request_context(
            headers=dict(Authorization=f"Bearer {access_token.access_token}"), environ_base={"REMOTE_ADDR": "127.0.0.1"}
        ):
            authenticate_request()

            self.assertEqual(member.member_id, g.user_id)
            self.assertCountEqual([USER, permission.permission], g.permissions)

        db_session.refresh(access_token)

        self.assertCountEqual([USER, permission.permission], access_token.permissions.split(","))

    def test_valid_service_auth_updates_access_token_and_sets_user_id_and_permission(self) -> None:
        access_token = self.db.create_access_token(user_id=TEST_SERVICE_USER_ID, expires=self.datetime(days=1))

        with self.app.test_request_context(
            headers=dict(Authorization=f"Bearer {access_token.access_token}"), environ_base={"REMOTE_ADDR": "127.0.0.1"}
        ):
            authenticate_request()

            self.assertEqual(TEST_SERVICE_USER_ID, g.user_id)
            self.assertCountEqual(ALL_PERMISSIONS, g.permissions)

        db_session.refresh(access_token)

        self.assertCountEqual(ALL_PERMISSIONS, access_token.permissions.split(","))

    def test_permission_is_required_for_view(self) -> None:
        with self.assertRaises(AssertionError):

            @self.service.route("/", method=GET, permission=None)
            def view() -> str:
                return ""

    def test_public_view_does_not_require_permissions(self) -> None:
        @self.service.route("/", method=GET, permission=PUBLIC)
        def view() -> str:
            return ""

        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            view()

        with self.app.test_request_context():
            g.user_id = TEST_SERVICE_USER_ID
            g.permissions = ALL_PERMISSIONS
            view()

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, "webshop")
            view()

    def test_logged_in_user_permission_check_works(self) -> None:
        @self.service.route("/", method=GET, permission=USER)
        def view() -> str:
            return ""

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, "webshop")
            view()

        with self.app.test_request_context():
            g.user_id = TEST_SERVICE_USER_ID
            g.permissions = ALL_PERMISSIONS
            with self.assertRaises(Forbidden):
                view()

        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            with self.assertRaises(Forbidden):
                view()

    def test_regular_permission_check_works(self) -> None:
        @self.service.route("/", method=GET, permission="webshop")
        def view() -> str:
            return ""

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, "webshop")
            view()

        with self.app.test_request_context():
            g.user_id = TEST_SERVICE_USER_ID
            g.permissions = ALL_PERMISSIONS
            view()

        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            with self.assertRaises(Forbidden):
                view()
