from multi_access.models import User


class MultiAccessMember(object):
    
    def __init__(self, user):
        self.user = user
        self.problems = []
        
        try:
            self.member_number = int(user.name)
        except (ValueError, TypeError) as e:
            self.member_number = None
            self.problems.append(f'bad "Identitet" (medlemsnummer) should be integer was "{user.name}"')

        
class EndTimestampDiff(object):
    
    def __init__(self, multi_access_member=None, maker_admin_member=None):
        self.multi_access_member = multi_access_member
        self.maker_admin_member = maker_admin_member


def get_multi_access_members(session, customer_id=16):
    """ Get relevant multi access members from database. """
    return [MultiAccessMember(u) for u in session.query(User).filter_by(customer_id=customer_id)]


def create_end_timestamp_diff(multi_access_users, maker_admin_members):
    """ Creates a list of diffing members ignoring everything but status and timestamp. The list conntains all
    members where multi access does not match maker admin. """
    print(multi_access_users)
    print(maker_admin_members)


def update_timestamps(end_timstamp_diff):
    """ Update all timestamps/status in maker admin included in the diff. Double checks that nothing changed in multi
    access since the member data was read (in this case raises exception). """
    pass
