from logging import getLogger

class AccessyMember():

    def __init__(self, member_number, user_id, membership_id, accessy_phone) -> None:
        self.user_id = user_id
        self.membership_id = membership_id
        self.accessy_phone = accessy_phone

    def __repr__(self):
        return f'AccessyMember(member_number={self.member_number}, user_id={self.user_id}, membership_id={self.membership_id}, accessy_phone={self.accessy_phone})'

class AccessyPermissiongroup():

    def __init__(self, permission_group_id) -> None:
        self.permission_group_id = permission_group_id
        self.week_end_date
        self.week_start_date