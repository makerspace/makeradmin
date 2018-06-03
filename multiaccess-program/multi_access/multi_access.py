from datetime import datetime, timedelta

from multi_access.models import User, AuthorityInUser, Authority, Customer


class DbMember(object):
    
    def __init__(self, user):
        self.user = user
        self.problems = []
        
        try:
            self.member_number = int(user.name)
        except (ValueError, TypeError) as e:
            self.member_number = None
            self.problems.append(f'bad "Identitet" (medlemsnummer) should be integer was "{user.name}"')


class BlockMember(object):
    """ Found a diffing member in multi access that needs to be blocked. """
    
    def __init__(self, db_member=None):
        self.db_member = db_member

    def describe_update(self):
        return f'blocking      #{self.db_member.user.name}, blocked False => True'
    
    def update(self, session, ui, customer_id=None, authority_id=None):
        user = session.query(User).get(self.db_member.user.id)
        user.blocked = True
        session.commit()
    
    def __eq__(self, other):
        return self.db_member == other.db_member


class UpdateMember(object):
    
    def __init__(self, db_member=None, ma_member=None):
        self.db_member = db_member
        self.ma_member = ma_member

        self.timestamp_diffs = self.timestamps_diff(ma_member.end_timestamp, db_member.user.stop_timestamp)
        self.tag_diffs = self.db_member.user.card != self.ma_member.rfid_tag

    @staticmethod
    def timestamps_diff(t1, t2):
        return abs(t1 - t2) > timedelta(seconds=1)

    def describe_update(self):
        res = f'member update #{self.ma_member.member_number} ({self.ma_member.firstname} {self.ma_member.lastname})'
        if self.timestamp_diffs:
            res += f', end timestamp {self.db_member.user.stop_timestamp} => {self.ma_member.end_timestamp}'
        if self.tag_diffs:
            res += f', tag {self.db_member.user.card} => {self.ma_member.rfid_tag}'
        return res
    
    def update(self, session, ui, customer_id=None, authority_id=None):
        user = session.query(User).get(self.db_member.user.id)
        user.stop_timestamp = self.ma_member.end_timestamp
        user.blocked = False
        user.card = self.ma_member.rfid_tag
        session.commit()
        
    def __eq__(self, other):
        return self.db_member == other.db_member and self.ma_member == other.ma_member
        

class AddMember(object):
    
    def __init__(self, ma_member=None):
        self.m = ma_member

    def describe_update(self):
        return (
            f'member add    #{self.m.member_number} ({self.m.firstname} {self.m.lastname})'
            f', tag {self.m.rfid_tag}, end timestamp {self.m.end_timestamp}'
        )

    def update(self, session, ui, customer_id=None, authority_id=None):
        ui.info__progress(self.describe_update())
        u = User(
            name=str(self.m.member_number),
            stop_timestamp=self.m.end_timestamp,
            card=self.m.rfid_tag,
            changed=0,
            customer_id=customer_id,
            created_timestamp=datetime.now(),
        )
        session.add(u)
        session.commit()
        session.add(AuthorityInUser(
            user_id=u.id,
            flags=0,
            authority_id=authority_id,
            removed_date=datetime(1900, 1, 1, 0, 0),
        ))
        session.commit()
        
    def __eq__(self, other):
        return self.m == other.m
        
        
def get_multi_access_members(session, customer_id):
    """ Get relevant multi access members from database. """
    return [DbMember(u) for u in session.query(User).filter_by(customer_id=customer_id)]


def diff_member_update(db_members, ma_members):
    """ Creates a list of diffing members ignoring everything but blocked and timestamp. The list contains all
    members where multi access does not match maker admin. Ignoring members that does not exist in either source.
    Blocked members should already have been filtered, making sure all ma_members are not blocked. """
    ma_members = {m.member_number: m for m in ma_members}
    db_members = {m.member_number: m for m in db_members}
    
    diffs = [
        UpdateMember(dbm, mam) for dbm, mam in
        ((db_members.get(m), ma_members.get(m)) for m in db_members.keys())
        if dbm and mam and (dbm.user.blocked
                            or dbm.user.card != mam.rfid_tag
                            or UpdateMember.timestamps_diff(dbm.user.stop_timestamp, mam.end_timestamp))
    ]
    return diffs


def diff_member_missing(db_members, ma_members):
    """ Creates a list of diffing members where the member exists in ma_members but not in db_members. """
    ma_dict = {m.member_number: m for m in ma_members}
    for m in db_members:
        ma_dict.pop(m.member_number, None)
    
    diffs = [AddMember(mam) for member_number, mam in ma_dict.items()]
    return diffs


def diff_blocked(db_members, ma_members):
    """ Creates a list of members that should not have access (not in ma_members). """
    db_dict = {m.member_number: m for m in db_members if not m.user.blocked}
    for m in ma_members:
        db_dict.pop(m.member_number, None)
    
    diffs = [BlockMember(dbm) for member_number, dbm in db_dict.items()]
    return diffs


def update_diffs(session, ui, diffs, customer_id=None, authority_id=None):
    # Sanity check customer_id and authority_id.
    customer = session.query(Customer).get(customer_id)
    if 'stockholm makerspace' not in customer.name.lower():
        raise Exception(f"Santicy check of customer id {customer_id} failed, expected 'Stockholm Makerspace'"
                        f" in name, was '{customer.name}'.")
                        
    authority = session.query(Authority).get(authority_id)
    if 'stockholm makerspace' not in authority.name.lower():
        raise Exception(f"Santicy check of authority id {authority_id} failed, expected 'Stockholm Makerspace'"
                        f" in name, was '{authority.name}'.")
    
    # Perform the updates.
    ui.info__progress("Updating members.")
    for diff in diffs:
        ui.info__progress(diff.describe_update())
        diff.update(session, ui, customer_id=customer_id, authority_id=authority_id)
    ui.info__progress("All members updated.")
