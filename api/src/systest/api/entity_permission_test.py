from core.auth import create_access_token
from membership.models import Permission
from service.api_definition import MEMBER_CREATE, MEMBER_DELETE, MEMBER_EDIT, MEMBER_VIEW
from service.db import db_session
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    # Not a full test of all permissions but a test that the generic permission mechanism works.

    @classmethod
    def create_token_with_permission(self, permission):
        """Return a logged in token that has a user with the given permission."""
        member = self.db.create_member()
        group = self.db.create_group()
        group.members.append(member)
        p = db_session.query(Permission).filter_by(permission=permission).first()
        group.permissions.append(p)
        res = create_access_token("", "", member.member_id)
        db_session.commit()
        return res["access_token"]

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.tokens = {
            p: self.create_token_with_permission(p) for p in [MEMBER_VIEW, MEMBER_CREATE, MEMBER_EDIT, MEMBER_DELETE]
        }

    def test_only_member_view_is_allowed_to_list(self):
        url = "/membership/member"
        self.api.get(url, token=self.tokens[MEMBER_VIEW]).expect(200)
        self.api.get(url, token=self.tokens[MEMBER_EDIT]).expect(403)
        self.api.get(url, token=self.tokens[MEMBER_CREATE]).expect(403)
        self.api.get(url, token=self.tokens[MEMBER_DELETE]).expect(403)

    def test_only_member_create_is_allowed_to_create(self):
        url = f"/membership/member"
        data = self.obj.create_member()
        self.api.post(url, data, token=self.tokens[MEMBER_VIEW]).expect(403)
        self.api.post(url, data, token=self.tokens[MEMBER_EDIT]).expect(403)
        self.api.post(url, data, token=self.tokens[MEMBER_CREATE]).expect(201)
        self.api.post(url, data, token=self.tokens[MEMBER_DELETE]).expect(403)

    def test_only_member_view_is_allowed_to_get(self):
        url = f"/membership/member/{self.db.create_member().member_id}"
        self.api.get(url, token=self.tokens[MEMBER_VIEW]).expect(200)
        self.api.get(url, token=self.tokens[MEMBER_EDIT]).expect(403)
        self.api.get(url, token=self.tokens[MEMBER_CREATE]).expect(403)
        self.api.get(url, token=self.tokens[MEMBER_DELETE]).expect(403)

    def test_only_member_edit_is_allowed_to_update(self):
        url = f"/membership/member/{self.db.create_member().member_id}"
        data = dict(firstname="Sune")
        self.api.put(url, data, token=self.tokens[MEMBER_VIEW]).expect(403)
        self.api.put(url, data, token=self.tokens[MEMBER_EDIT]).expect(200)
        self.api.put(url, data, token=self.tokens[MEMBER_CREATE]).expect(403)
        self.api.put(url, data, token=self.tokens[MEMBER_DELETE]).expect(403)

    def test_only_member_delete_is_allowed_to_delete(self):
        url = f"/membership/member/{self.db.create_member().member_id}"
        self.api.delete(url, token=self.tokens[MEMBER_VIEW]).expect(403)
        self.api.delete(url, token=self.tokens[MEMBER_EDIT]).expect(403)
        self.api.delete(url, token=self.tokens[MEMBER_CREATE]).expect(403)
        self.api.delete(url, token=self.tokens[MEMBER_DELETE]).expect(200)
