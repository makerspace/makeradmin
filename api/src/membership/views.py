from membership import service
from membership.membership import get_membership_smmary, add_membership_days
from membership.models import Member, Group, member_group, Span, Permission, register_permissions, group_permission, \
    Key, MEMBERSHIP, LABACCESS, SPECIAL_LABACESS
from service.api_definition import MEMBER_VIEW, MEMBER_CREATE, MEMBER_EDIT, MEMBER_DELETE, GROUP_VIEW, GROUP_CREATE, \
    GROUP_EDIT, GROUP_DELETE, GROUP_MEMBER_VIEW, GROUP_MEMBER_ADD, GROUP_MEMBER_REMOVE, SPAN_VIEW, SPAN_MANAGE, \
    PERMISSION_MANAGE, SERVICE, POST, Arg, symbol_list, PERMISSION_VIEW, KEY_VIEW, KEY_EDIT, GET, Enum, natural0, \
    iso_date, non_empty_str, natural1
from service.db import db_session
from service.entity import Entity, not_empty, ASC, DESC, MemberEntity, OrmManyRelation, OrmSingeRelation

# TODO BM Move implementations around.

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
    return get_membership_smmary(entity_id)


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
    path="/group/<int:related_entity_id>/permisssions",
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
    permission_list=KEY_VIEW,
    permission_read=KEY_VIEW,
    permission_create=KEY_EDIT,
    permission_update=KEY_EDIT,
    permission_delete=KEY_EDIT,
)

# TODO BM Complete all membership api.

# Special? Check if they are used?
# DONE $app->  post("membership/member/{id}/activate", ['middleware' => 'permission:service', 'uses' => "Member@activate"]); // Model: Activate
# NOT USED $app->  post("membership/member/{id}/addMembershipSpan",    ['middleware' => 'permission:member_edit', 'uses' => "Member@addMembershipSpan"]);
# DONE $app->  post("membership/member/{id}/addMembershipDays",    ['middleware' => 'permission:member_edit', 'uses' => "Member@addMembershipDays"]);
# DONE $app->  get("membership/member/{id}/membership",    ['middleware' => 'permission:member_view', 'uses' => "Member@getMembership"]); // Get if a member has an active membership
# DONE $app->  post("membership/permission/register", "Permission@batchRegister");
# Special since it is a relation in two steps.
# $app->   get("membership/member/{id}/permissions",   ['middleware' => 'permission:permission_view',     'uses' => "Member@getPermissions"]);    // Get a member's permissions

# DONE Entity
# DONE $app->   get("membership/member",      ['middleware' => 'permission:member_view',   'uses' => "Member@list"]);   // Get collection
# DONE  $app->  post("membership/member",      ['middleware' => 'permission:member_create', 'uses' => "Member@create"]); // Model: Create
# DONE  $app->   get("membership/member/{id}", ['middleware' => 'permission:member_view',   'uses' => "Member@read"]);   // Model: Read
# DONE  $app->   put("membership/member/{id}", ['middleware' => 'permission:member_edit',   'uses' => "Member@update"]); // Model: Update
# DONE  $app->delete("membership/member/{id}", ['middleware' => 'permission:member_delete', 'uses' => "Member@delete"]); // Model: Delete
# Relation
# DONE $app->   get("membership/member/{id}/groups",        ['middleware' => 'permission:group_member_view',   'uses' => "Member@getGroups"]);    // Get collection with members
# DONE $app->  post("membership/member/{id}/groups/add",    ['middleware' => 'permission:group_member_add',    'uses' => "Member@addGroup"]);    // Get collection with members
# DONE $app->  post("membership/member/{id}/groups/remove", ['middleware' => 'permission:group_member_remove', 'uses' => "Member@removeGroup"]);    // Get collection with members
# Relation
# DONE $app->   get("membership/member/{id}/keys", ['middleware' => 'permission:member_view',   'uses' => "Member@getKeys"]);

# Entity
# DONE $app->   get("membership/key",      ['middleware' => 'permission:keys_view', 'uses' => "Key@list"]);   // Get collection
# DONE $app->  post("membership/key",      ['middleware' => 'permission:keys_edit', 'uses' => "Key@create"]); // Model: Create
# DONE $app->   get("membership/key/{id}", ['middleware' => 'permission:keys_view', 'uses' => "Key@read"]);   // Model: Read
# DONE $app->   put("membership/key/{id}", ['middleware' => 'permission:keys_edit', 'uses' => "Key@update"]); // Model: Update
# DONE $app->delete("membership/key/{id}", ['middleware' => 'permission:keys_edit', 'uses' => "Key@delete"]); // Model: Delete

# Entity
# DONE $app->   get("membership/span",      ['middleware' => 'permission:span_view',  'uses' => "Span@list"]);       // Get collection
# DONE $app->  post("membership/span",      ['middleware' => 'permission:span_manage',  'uses' => "Span@create"]);   // Model: Create
# DONE $app->   get("membership/span/{id}", ['middleware' => 'permission:span_view',  'uses' => "Span@read"]);       // Model: Read
# DONE $app->   put("membership/span/{id}", ['middleware' => 'permission:span_manage',  'uses' => "Span@update"]);   // Model: Update
# DONE $app->delete("membership/span/{id}", ['middleware' => 'permission:span_manage',  'uses' => "Span@delete"]);   // Model: Delete

# DONE Entity
# DONE $app->   get("membership/group",       ['middleware' => 'permission:group_view',   'uses' => "Group@list"]);    // Get collection
# DONE $app->  post("membership/group",       ['middleware' => 'permission:group_create', 'uses' => "Group@create"]);  // Model: Create
# DONE $app->   get("membership/group/{id}",  ['middleware' => 'permission:group_view',   'uses' => "Group@read"]);    // Model: Read
# DONE $app->   put("membership/group/{id}",  ['middleware' => 'permission:group_edit',   'uses' => "Group@update"]);  // Model: Update
# DONE $app->delete("membership/group/{id}",  ['middleware' => 'permission:group_delete', 'uses' => "Group@delete"]);  // Model: Delete
# Relation
# DONE $app->   get("membership/group/{id}/members",        ['middleware' => 'permission:group_member_view',   'uses' => "Group@getMembers"]);    // Get collection with members
# DONE $app->  post("membership/group/{id}/members/add",    ['middleware' => 'permission:group_member_add',    'uses' => "Group@addMembers"]);
# DONE $app->  post("membership/group/{id}/members/remove", ['middleware' => 'permission:group_member_remove', 'uses' => "Group@removeMembers"]);
# Relation
# DONE $app->   get("membership/group/{id}/permissions",        ['middleware' => 'permission:permission_view',   'uses' => "Group@listPermissions"]);  // Model: Create
# DONE $app->  post("membership/group/{id}/permissions/add",    ['middleware' => 'permission:permission_manage', 'uses' => "Group@addPermissions"]);  // Model: Create
# DONE $app->  post("membership/group/{id}/permissions/remove", ['middleware' => 'permission:permission_manage', 'uses' => "Group@removePermissions"]);  // Model: Create

# Entity
# DONE $app->   get("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@list"]);     // Get collection
# DONE $app->  post("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@create"]);   // Model: Create
# DONE $app->   get("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@read"]);     // Model: Read
# DONE $app->   put("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@update"]);   // Model: Update
# DONE $app->delete("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@delete"]);   // Model: Delete

# IGNORE // Roles
# IGNORE $app->   get("membership/role",        "Role@list");     // Get collection
# IGNORE $app->  post("membership/role",        "Role@create");   // Model: Create
# IGNORE $app->   get("membership/role/{id}",   "Role@read");     // Model: Read
# IGNORE $app->   put("membership/role/{id}",   "Role@update");   // Model: Update
# IGNORE $app->delete("membership/role/{id}",   "Role@delete");   // Model: Delete

# NOT USED $app->  post("membership/authenticate", "Member@authenticate");   // Authenticate a member

