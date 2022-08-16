#!/usr/bin/env python3
from logging import basicConfig, INFO, getLogger

from accessy import AccessyMember, AccessyPermissiongroup
from membership.models import Member as MakerAdminMember
from membership.membership import get_members_and_membership

logger = getLogger("makeradmin")

ORG_MEMBER_COUNT_LIMIT = 600

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

def sync():
    #TODO populate these lists
    accessy_org_members
    accessy_persmission_group_members
    ma_members, ma_memberships = get_members_and_membership()

    #Filter the members
    members_in_both, members_not_in_makeradmin = split_into_groups(accessy_org_members, ma_members)
    
    #Delete accessy members not in makeradmin from accessy
    for acessy_member in members_not_in_makeradmin:
        removeFromGroup(acessy_member)
        delete_member(acessy_member)

    #Remove members from the permission group if are not members of org
    for accessy_member in accessy_persmission_group_members:
        if notInOrg(accessy_member) or not hasLabbAccess(makeradmin_member):
            removeFromGroup(accessy_member)

    #Add and remove people that are in the org from the group based on labbaccess
    for accessy_member, makeradmin_member in members_in_both:
        if notInGroup(accessy_member) and hasLabbAccess(makeradmin_member):
            addToGroup(accessy_member)
        elif inGroup(accessy_member) and not hasLabbAccess(makeradmin_member):
            removeFromGroup(accessy_member)

    #Check org membership count, remove if above limit (600), don't remove people with access to the space. LIFO based on last labbaccess and membership
    if len(accessy_org_members) > ORG_MEMBER_COUNT_LIMIT:
        remove_old()

    return

def main():
    print("test")

if __name__ == '__main__':
    main()