from membership import service
from membership.member_entity import MemberEntity
from membership.membership import get_membership_summary, add_membership_days
from membership.models import Member, Group, member_group, Span, Permission, group_permission, \
    Key, MEMBERSHIP, LABACCESS, SPECIAL_LABACESS
from membership.member_auth import get_member_permissions
from membership.permissions import register_permissions
from service.api_definition import MEMBER_VIEW, MEMBER_CREATE, MEMBER_EDIT, MEMBER_DELETE, GROUP_VIEW, GROUP_CREATE, \
    GROUP_EDIT, GROUP_DELETE, GROUP_MEMBER_VIEW, GROUP_MEMBER_ADD, GROUP_MEMBER_REMOVE, SPAN_VIEW, SPAN_MANAGE, \
    PERMISSION_MANAGE, SERVICE, POST, Arg, symbol_list, PERMISSION_VIEW, KEYS_VIEW, KEYS_EDIT, GET, Enum, \
    iso_date, non_empty_str, natural1
from service.db import db_session
from service.entity import Entity, not_empty, ASC, DESC, OrmManyRelation, OrmSingeRelation

# TODO BM Bug, can't create member zipcode not handled correctly in gui.
member_entity = MemberEntity(
    Member,
    validation=dict(email=not_empty, firstname=not_empty),
    default_sort_column='member_number',
    default_sort_order=DESC,
    hidden_columns=('password',),
    search_columns=('firstname', 'lastname', 'email', 'address_street', 'address_extra', 'address_zipcode',
                    'address_city', 'phone', 'civicregno', 'member_number'),
)

group_entity = Entity(
    Group,
    validation=dict(name=not_empty, title=not_empty),
    default_sort_column='title',
    default_sort_order=ASC,
    search_columns=('name', 'title', 'description'),
    read_only_columns=('parent', 'left', 'right'),
    hidden_columns=('parent', 'left', 'right'),
)

# TODO BM Add tests.
permission_entity = Entity(
    Permission,
    default_sort_column='permission_id',
    default_sort_order=DESC,
    search_columns=('permission', 'permission_id'),
)

# TODO BM got expandable field member (a concept used in two places)
span_entity = Entity(
    Span,
    default_sort_column='created_at',
    default_sort_order=DESC,
    search_columns=('member_id',),
    list_deleted=True,  # TODO BM Add test for this (and general tests).
)

# TODO BM got expandable field member (a concept used in two places)
key_entity = Entity(
    Key,
    default_sort_column='created_at',
    default_sort_order=DESC,
    search_columns=('description', 'tagid'),
)


service.entity_routes(
    path="/member",
    entity=member_entity,
    permission_list=MEMBER_VIEW,
    permission_read=MEMBER_VIEW,
    permission_create=MEMBER_CREATE,
    permission_update=MEMBER_EDIT,
    permission_delete=MEMBER_DELETE,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/groups",
    entity=group_entity,
    relation=OrmManyRelation('groups', Group.members, member_group, 'group_id', 'member_id'),
    permission_list=GROUP_MEMBER_VIEW,
    permission_add=GROUP_MEMBER_ADD,
    permission_remove=GROUP_MEMBER_REMOVE,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/keys",
    entity=key_entity,
    relation=OrmSingeRelation('keys', 'member_id'),
    permission_list=MEMBER_VIEW,
)


service.related_entity_routes(
    path="/member/<int:related_entity_id>/spans",
    entity=span_entity,
    relation=OrmSingeRelation('spans', 'member_id'),
    permission_list=SPAN_VIEW,
)


@service.route("/member/<int:entity_id>/activate", method=POST, permission=SERVICE, status='activated')
def member_activate(entity_id=None):
    """ Activate (undelete) a member. """
    db_session.query(Member).filter_by(member_id=entity_id).update({'deleted_at': None})


@service.route("/member/<int:entity_id>/addMembershipDays", method=POST, permission=MEMBER_EDIT)
def member_add_membership_days(
        entity_id=None, type=Arg(Enum(MEMBERSHIP, LABACCESS, SPECIAL_LABACESS)), days=Arg(natural1),
        creation_reason=Arg(non_empty_str), default_start_date=Arg(iso_date, required=False)):
    return add_membership_days(entity_id, type, days, creation_reason, default_start_date)


@service.route("/member/<int:entity_id>/membership", method=GET, permission=MEMBER_VIEW)
def member_get_membership(entity_id=None):
    return get_membership_summary(entity_id)


@service.route("/member/<int:entity_id>/permissions", method=GET, permission=PERMISSION_VIEW)
def member_get_permissions(entity_id=None):
    return [{'permission_id': i, 'permission': p} for i, p in get_member_permissions(entity_id)]


service.entity_routes(
    path="/group",
    entity=group_entity,
    permission_list=GROUP_VIEW,
    permission_read=GROUP_VIEW,
    permission_create=GROUP_CREATE,
    permission_update=GROUP_EDIT,
    permission_delete=GROUP_DELETE,
)

service.related_entity_routes(
    path="/group/<int:related_entity_id>/members",
    entity=member_entity,
    relation=OrmManyRelation('members', Member.groups, member_group, 'member_id', 'group_id'),
    permission_list=GROUP_MEMBER_VIEW,
    permission_add=GROUP_MEMBER_ADD,
    permission_remove=GROUP_MEMBER_REMOVE,
)

service.related_entity_routes(
    path="/group/<int:related_entity_id>/permissions",
    entity=permission_entity,
    relation=OrmManyRelation('permisssions', Group.permissions, group_permission, 'group_id', 'permission_id'),
    permission_list=PERMISSION_VIEW,
    permission_add=PERMISSION_MANAGE,
    permission_remove=PERMISSION_MANAGE,
)

service.entity_routes(
    path="/permission",
    entity=permission_entity,
    permission_list=PERMISSION_MANAGE,  # TODO Why not view?
    permission_read=PERMISSION_MANAGE,  # TODO Vhy not view?
    permission_create=PERMISSION_MANAGE,
    permission_update=PERMISSION_MANAGE,
    permission_delete=PERMISSION_MANAGE,
)


@service.route("/membership/permission/register", method=POST, permission=SERVICE)
def permissions_register(permissions=Arg(symbol_list)):
    """ Register permissions that a service is dependent of. """
    register_permissions(permissions)


service.entity_routes(
    path="/span",
    entity=span_entity,
    permission_list=SPAN_VIEW,
    permission_read=SPAN_VIEW,
    permission_create=SPAN_MANAGE,
    permission_update=SPAN_MANAGE,
    permission_delete=SPAN_MANAGE,
)


service.entity_routes(
    path="/key",
    entity=key_entity,
    permission_list=KEYS_VIEW,
    permission_read=KEYS_VIEW,
    permission_create=KEYS_EDIT,
    permission_update=KEYS_EDIT,
    permission_delete=KEYS_EDIT,
)
