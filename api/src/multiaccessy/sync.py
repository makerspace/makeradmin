#!/usr/bin/env python3
import argparse
import sys

import psutil
from logging import basicConfig, INFO, getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from accessy import AccessyMember, AccessyPermissiongroup
from membership.models import Member as MakerAdminMember

try:
    from source_revision import source_revision
except ImportError:
    source_revision = 'unknown'

logger = getLogger("makeradmin")


WHAT_ORDERS = 'orders'
WHAT_UPDATE = 'update'
WHAT_ADD = 'add'
WHAT_BLOCK = 'block'
WHAT_ALL = {WHAT_ORDERS, WHAT_UPDATE, WHAT_ADD, WHAT_BLOCK}


def split_into_groups(accessy_members:list[AccessyMember], makeradmin_members:list[MakerAdminMember]):
    members_ok = []
    members_not_in_makeradmin = []
    accessy_members.sort(key=lambda x: x.accessy_phone)
    makeradmin_members.sort(key=lambda x: x.phone)

    #Check if members are in accessy but not makeradmin
    for acessy_member in accessy_members:
        found = False
        for makeradmin_member in makeradmin_members:
            if acessy_member.accessy_phone == makeradmin_member.phone:
                members_ok.append({acessy_member, makeradmin_member})
                found = True
                break
        if not found:
            members_not_in_makeradmin.append(acessy_member)
    
    return members_ok, members_not_in_makeradmin

def update_regular_access(permission_groups: list[AccessyPermissiongroup], acessy_member:AccessyMember, makeradmin_member:MakerAdminMember):
    for permission_group in permission_groups:
        if permission_group.week_start_date < makeradmin_member.end_timestamp:
            add_to_permission_group(permission_group, acessy_member) #TODO

def sync(session=None, client=None, ui=None, customer_id=None, authority_id=None, what=None, ignore_running=False):
    what = what or WHAT_ALL

    # Log in to the MakerAdmin server unless we are already logged in
    if not client.is_logged_in():
        while not client.login():
            pass

    # Run actions on MakerAdmin (ship orders and update key timestamps)

    if WHAT_ORDERS in what:
        #TODO update pending lab stuff
        client.ship_orders(ui) #TODO should only run once a week etc

    # Fetch from MakerAdmin
    
    ma_members = client.fetch_members(ui)

    #TODO update access permision groups

    #TODO list members

    #Split the members into groups
    members_ok, members_not_in_makeradmin = split_into_groups(accessy_members, ma_members)
    
    #Remove accessy members not in makeradmin from accessy
    for acessy_member in members_not_in_makeradmin:
        remove_member(acessy_member) #TODO

    #Update member access permission groups
    for acessy_member, makeradmin_member in members_ok:
        update_regular_access(acessy_member,makeradmin_member)
        #TODO special groups

    return

def main():

    basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
                stream=sys.stderr, level=INFO)

    parser = argparse.ArgumentParser("Fetches member list from makeradmin.se or local file, then prompt user with"
                                     f" changes to make. Built from source revision {source_revision}.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-w", "--what", default=",".join(WHAT_ALL),
                        help=f"What to update, comma separated list."
                             f" '{WHAT_ORDERS}' tell maker admin to perform order actions before updating members."
                             f" '{WHAT_UPDATE}' will update end times and rfid_tag."
                             f" '{WHAT_ADD}' will add members in MultAccess."
                             f" '{WHAT_BLOCK}' will block members that should not have access."
                        )
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makerspace.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("-m", "--members-filename", default=None,
                        help="Provide members in a file instead of fetching from maker admin (same format as response"
                             " from maker admin).")
    parser.add_argument("-t", "--token", default="",
                        help="Provide token on command line instead of prompting for login.")
    
    args = parser.parse_args()

    what = args.what.split(',')
    for w in what:
        if w not in WHAT_ALL:
            raise argparse.ArgumentError(f"Unknown argument '{w}' to what.")

    with Tui() as ui:
        client = MakerAdminClient(ui=ui, base_url=args.maker_admin_base_url, members_filename=args.members_filename,
                                  token=args.token)

        ui.info__progress(f"connecting to {args.db}")
        engine = create_engine(args.db)

        while True:
            Session = sessionmaker(bind=engine)
            session = Session()
            
            sync(session=session, ui=ui, client=client, customer_id=args.customer_id, authority_id=args.authority_id,
                 ignore_running=args.ignore_running, what=what)

            session.close()
            
            ui.prompt__run_again()
            

if __name__ == '__main__':

    main()
