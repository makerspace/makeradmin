from multi_access.models import User


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

        self.blocked_diffs = ma_member.blocked != db_member.user.blocked
        self.timestamp_diffs = ma_member.end_timestamp != db_member.user.stop_timestamp

    def describe_update(self):
        res = f'member #{self.ma_member.member_number} ({self.ma_member.firstname} {self.ma_member.lastname})'
        
        if self.timestamp_diffs:
            res += f', end timestamp {self.db_member.user.stop_timestamp} => {self.ma_member.end_timestamp}'
        
        if self.blocked_diffs:
            res += f', blocked {self.db_member.user.blocked} => {self.ma_member.blocked}'
            
        return res
    
    def update(self, session, ui):
        ui.info__progress(f'updating: {self.describe_update()}')
        user = session.query(User).get(self.db_member.user.id)
        user.stop_timestamp = self.ma_member.end_timestamp
        user.blocked = self.ma_member.blocked
        
        
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
        if dbm and mam and (dbm.user.blocked != mam.blocked or dbm.user.stop_timestamp != mam.end_timestamp)
    ]
    return diffs


def update_diffs(session, ui, diffs):
    for diff in diffs:
        diff.update(session, ui)
