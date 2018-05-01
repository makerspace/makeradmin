
class MultiAccessMember(object):
    pass


class EndTimestampDiff(object):
    pass


def get_multi_access_members(session):
    """ Get relevant multi access members from database. """
    pass


def create_end_timestamp_diff(multi_access_members, maker_admin_members):
    """ Creates a list of diffing members ignoring everything but status and timestamp. The list conntains all
    members where multi access does not match maker admin. """
    pass


def update_timestamps(end_timstamp_diff):
    """ Update all timestamps/status in maker admin included in the diff. Double checks that nothing changed in multi
    access since the member data was read (in this case raises exception). """
    pass