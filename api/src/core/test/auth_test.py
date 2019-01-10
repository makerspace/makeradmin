from flask import g

import core
import membership

from core import models
from core.auth import authenticate_request
from core.models import AccessToken
from service.api_definition import USER, SERVICE, GET, PUBLIC, SERVICE_USER_ID
from service.db import db_session
from service.error import Unauthorized, Forbidden
from test_aid.test_base import FlaskTestBase


class Test(FlaskTestBase):

    models = [core.models, membership.models]
    
    def test_user_id_and_permission_is_set_even_if_there_is_no_auth_header(self):
        with self.app.test_request_context():
            self.assertFalse(hasattr(g, 'user_id'))
            self.assertFalse(hasattr(g, 'permissions'))
            
            authenticate_request()
            
            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_no_auth_header_sets_correct_user_and_permissions(self):
        with self.app.test_request_context():
            authenticate_request()
            
            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_empty_auth_or_bad_header_raises_unauthorized(self):
        with self.app.test_request_context(headers=dict(Authorization='')):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

        with self.app.test_request_context(headers=dict(Authorization='dkopwkdw')):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_non_existing_access_token_raises_unauthorized(self):
        self.db.create_access_token(user_id=1)
        
        with self.app.test_request_context(headers=dict(Authorization='Bearer non-existent-token')):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)

    def test_expired_token_raises_unautorized_and_removes_all_expired_tokens(self):
        self.db.create_access_token(user_id=1, access_token='expired-1', expires=self.datetime(days=-1))
        self.db.create_access_token(user_id=2, access_token='expired-2', expires=self.datetime(days=-1))
        self.db.create_access_token(user_id=3, access_token='not-expired-1', expires=self.datetime(days=1))
    
        with self.app.test_request_context(headers=dict(Authorization='Bearer expired-1')):
            with self.assertRaises(Unauthorized):
                authenticate_request()

            self.assertIsNone(g.user_id)
            self.assertEqual(tuple(), g.permissions)
        
        access_token, = db_session.query(AccessToken).all()
        
        self.assertEqual('not-expired-1', access_token.access_token)
    
    def test_valid_user_auth_updates_access_token_and_sets_user_id_and_permission(self):
        permission = self.db.create_permission()
        member = self.db.create_member()
        group = self.db.create_group()
        group.members.append(member)
        group.permissions.append(permission)
        
        access_token = self.db.create_access_token(user_id=member.member_id, expires=self.datetime(days=1))

        with self.app.test_request_context(headers=dict(Authorization=f'Bearer {access_token.access_token}'),
                                           environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            authenticate_request()

            self.assertEqual(member.member_id, g.user_id)
            self.assertCountEqual([USER, permission.permission], g.permissions)
    
        db_session.refresh(access_token)
        
        self.assertCountEqual([USER, permission.permission], access_token.permissions.split(','))

    def test_valid_service_auth_updates_access_token_and_sets_user_id_and_permission(self):
        access_token = self.db.create_access_token(user_id=SERVICE_USER_ID, expires=self.datetime(days=1))

        with self.app.test_request_context(headers=dict(Authorization=f'Bearer {access_token.access_token}'),
                                           environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            authenticate_request()

            self.assertEqual(SERVICE_USER_ID, g.user_id)
            self.assertCountEqual([SERVICE], g.permissions)
    
        db_session.refresh(access_token)
    
        self.assertEqual(SERVICE, access_token.permissions)
    
    def test_permission_is_required_for_view(self):
        with self.assertRaises(AssertionError):
            @self.service.route('/', method=GET, permission=None)
            def view():
                pass

    def test_public_view_does_not_require_permissions(self):
        @self.service.route('/', method=GET, permission=PUBLIC)
        def view():
            pass
        
        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            view()

        with self.app.test_request_context():
            g.user_id = SERVICE_USER_ID
            g.permissions = (SERVICE,)
            view()

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, 'webshop')
            view()

    def test_service_permission_check_works(self):
        @self.service.route('/', method=GET, permission=SERVICE)
        def view():
            pass

        with self.app.test_request_context():
            g.user_id = SERVICE_USER_ID
            g.permissions = (SERVICE,)
            view()
        
        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            with self.assertRaises(Forbidden):
                view()

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, 'webshop')
            with self.assertRaises(Forbidden):
                view()

    def test_logged_in_user_permission_check_works(self):
        @self.service.route('/', method=GET, permission=USER)
        def view():
            pass

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, 'webshop')
            view()

        with self.app.test_request_context():
            g.user_id = SERVICE_USER_ID
            g.permissions = (SERVICE,)
            with self.assertRaises(Forbidden):
                view()
        
        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            with self.assertRaises(Forbidden):
                view()

    def test_regular_permission_check_works(self):
        @self.service.route('/', method=GET, permission='webshop')
        def view():
            pass

        with self.app.test_request_context():
            g.user_id = 1
            g.permissions = (USER, 'webshop')
            view()

        with self.app.test_request_context():
            g.user_id = SERVICE_USER_ID
            g.permissions = (SERVICE,)
            view()
        
        with self.app.test_request_context():
            g.user_id = None
            g.permissions = tuple()
            with self.assertRaises(Forbidden):
                view()
