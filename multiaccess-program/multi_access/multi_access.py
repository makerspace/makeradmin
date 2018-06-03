from datetime import datetime, timedelta

from multi_access.models import User, AuthorityInUser, Authority, Customer


# TODO Add changing of key.


class DbMember(object):
    
    def __init__(self, user):
        self.user = user
        self.problems = []
        
        try:
            self.member_number = int(user.name)
        except (ValueError, TypeError) as e:
            self.member_number = None
            self.problems.append(f'bad "Identitet" (medlemsnummer) should be integer was "{user.name}"')

    
class EndTimestampDiff(object):
    
    def __init__(self, db_member=None, ma_member=None):
        self.db_member = db_member
        self.ma_member = ma_member

        self.blocked_diffs = ma_member.blocked != bool(db_member.user.blocked)  # In multi access NULL means false.
        self.timestamp_diffs = self.timestamps_diff(ma_member.end_timestamp, db_member.user.stop_timestamp)
        # TODO Add test for no diff i same second.

    @staticmethod
    def timestamps_diff(t1, t2):
        return abs(t1 - t2) > timedelta(seconds=1)

    def describe_update(self):
        res = f'update #{self.ma_member.member_number} ({self.ma_member.firstname} {self.ma_member.lastname})'
        
        if self.timestamp_diffs:
            res += f', end timestamp {self.db_member.user.stop_timestamp} => {self.ma_member.end_timestamp}'
        
        if self.blocked_diffs:
            res += f', blocked {self.db_member.user.blocked} => {self.ma_member.blocked}'
            
        return res
    
    def update(self, session, ui, customer_id=None, authority_id=None):
        ui.info__progress(f'updating {self.describe_update()}')
        user = session.query(User).get(self.db_member.user.id)
        user.stop_timestamp = self.ma_member.end_timestamp
        user.blocked = self.ma_member.blocked
        session.commit()
        
    def __eq__(self, other):
        return self.db_member == other.db_member and self.ma_member == other.ma_member
        

class MemberMissingDiff(object):
    
    def __init__(self, ma_member=None):
        self.m = ma_member

    def describe_update(self):
        return (
            f'add     #{self.m.member_number} ({self.m.firstname} {self.m.lastname})'
            f', tag {self.m.rfid_tag}, end timestamp {self.m.end_timestamp}, blocked {self.m.blocked}'
        )
    
    def update(self, session, ui, customer_id=None, authority_id=None):
        ui.info__progress(self.describe_update())
        u = User(
            name=str(self.m.member_number),
            stop_timestamp=self.m.end_timestamp,
            card=self.m.rfid_tag,
            blocked=self.m.blocked,
            changed=False,
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


def create_end_timestamp_diff(db_members, ma_members):
    """ Creates a list of diffing members ignoring everything but blocked and timestamp. The list contains all
    members where multi access does not match maker admin. Ignoring members that does not exist in either source. """
    ma_members = {m.member_number: m for m in ma_members}
    db_members = {m.member_number: m for m in db_members}
    
    diffs = [
        EndTimestampDiff(dbm, mam) for dbm, mam in
        ((db_members.get(m), ma_members.get(m)) for m in db_members.keys())
        if dbm and mam and (dbm.user.blocked != mam.blocked or
                            EndTimestampDiff.timestamps_diff(dbm.user.stop_timestamp, mam.end_timestamp))
    ]
    return diffs


def create_member_diff(db_members, ma_members):
    """ Creates a list of diffing members where the member exists in ma_members but not in db_members. """
    ma_members = {m.member_number: m for m in ma_members}
    for m in db_members:
        ma_members.pop(m.member_number, None)
    
    diffs = [MemberMissingDiff(mam) for member_number, mam in ma_members.items()]
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
    for diff in diffs:
        diff.update(session, ui, customer_id=customer_id, authority_id=authority_id)
