from membership import service
from membership.models import Member, Group
from service.api_definition import MEMBER_VIEW, MEMBER_CREATE, MEMBER_EDIT, MEMBER_DELETE, GROUP_VIEW, GROUP_CREATE, \
    GROUP_EDIT, GROUP_DELETE, GROUP_MEMBER_VIEW, GROUP_MEMBER_ADD, GROUP_MEMBER_REMOVE
from service.entity import Entity, not_empty, ASC, DESC, MemberEntity, OrmPropertyRelation

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

service.entity_routes(
    path="/member",
    entity=member_entity,
    permission_list=MEMBER_VIEW,
    permission_create=MEMBER_CREATE,
    permission_read=MEMBER_VIEW,
    permission_update=MEMBER_EDIT,
    permission_delete=MEMBER_DELETE,
)

# TODO BM Group contains num_members that is calculated from relation, but only for list or related list.
group_entity = Entity(
    Group,
    validation=dict(name=not_empty, title=not_empty),
    default_sort_column='title',
    default_sort_order=ASC,
    search_columns=('name', 'title', 'description'),
    read_only_columns=('parent', 'left', 'right'),
    hidden_columns=('parent', 'left', 'right'),
)

service.entity_routes(
    path="/group",
    entity=group_entity,
    permission_list=GROUP_VIEW,
    permission_create=GROUP_CREATE,
    permission_read=GROUP_VIEW,
    permission_update=GROUP_EDIT,
    permission_delete=GROUP_DELETE,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/groups",
    entity=group_entity,
    relation=OrmPropertyRelation("member", Group, 'members'),
    permission_list=GROUP_MEMBER_VIEW,
    permission_add=GROUP_MEMBER_ADD,
    permission_remove=GROUP_MEMBER_REMOVE,
)


# TODO BM Complete all membership api.

# Special? Check if they are used?
# $app->  post("membership/member/{id}/activate", ['middleware' => 'permission:service', 'uses' => "Member@activate"]); // Model: Activate
# $app->  post("membership/member/{id}/addMembershipSpan",    ['middleware' => 'permission:member_edit', 'uses' => "Member@addMembershipSpan"]);
# $app->  post("membership/member/{id}/addMembershipDays",    ['middleware' => 'permission:member_edit', 'uses' => "Member@addMembershipDays"]);
# $app->  get("membership/member/{id}/membership",    ['middleware' => 'permission:member_view', 'uses' => "Member@getMembership"]); // Get if a member has an active membership
# $app->  post("membership/permission/register", "Permission@batchRegister");
# Special since it is a relation in two steps.
# $app->   get("membership/member/{id}/permissions",   ['middleware' => 'permission:permission_view',     'uses' => "Member@getPermissions"]);    // Get a member's permissions

# DONE Entity
# DONE $app->   get("membership/member",      ['middleware' => 'permission:member_view',   'uses' => "Member@list"]);   // Get collection
# DONE  $app->  post("membership/member",      ['middleware' => 'permission:member_create', 'uses' => "Member@create"]); // Model: Create
# DONE  $app->   get("membership/member/{id}", ['middleware' => 'permission:member_view',   'uses' => "Member@read"]);   // Model: Read
# DONE  $app->   put("membership/member/{id}", ['middleware' => 'permission:member_edit',   'uses' => "Member@update"]); // Model: Update
# DONE  $app->delete("membership/member/{id}", ['middleware' => 'permission:member_delete', 'uses' => "Member@delete"]); // Model: Delete
# Relation
# $app->   get("membership/member/{id}/groups",        ['middleware' => 'permission:group_member_view',   'uses' => "Member@getGroups"]);    // Get collection with members
# $app->  post("membership/member/{id}/groups/add",    ['middleware' => 'permission:group_member_add',    'uses' => "Member@addGroup"]);    // Get collection with members
# $app->  post("membership/member/{id}/groups/remove", ['middleware' => 'permission:group_member_remove', 'uses' => "Member@removeGroup"]);    // Get collection with members
# Relation
# $app->   get("membership/member/{id}/keys", ['middleware' => 'permission:member_view',   'uses' => "Member@getKeys"]);

# Entity
# $app->   get("membership/key",      ['middleware' => 'permission:keys_view', 'uses' => "Key@list"]);   // Get collection
# $app->  post("membership/key",      ['middleware' => 'permission:keys_edit', 'uses' => "Key@create"]); // Model: Create
# $app->   get("membership/key/{id}", ['middleware' => 'permission:keys_view', 'uses' => "Key@read"]);   // Model: Read
# $app->   put("membership/key/{id}", ['middleware' => 'permission:keys_edit', 'uses' => "Key@update"]); // Model: Update
# $app->delete("membership/key/{id}", ['middleware' => 'permission:keys_edit', 'uses' => "Key@delete"]); // Model: Delete

# Entity
# $app->   get("membership/span",      ['middleware' => 'permission:span_view',  'uses' => "Span@list"]);       // Get collection
# $app->  post("membership/span",      ['middleware' => 'permission:span_manage',  'uses' => "Span@create"]);   // Model: Create
# $app->   get("membership/span/{id}", ['middleware' => 'permission:span_view',  'uses' => "Span@read"]);       // Model: Read
# $app->   put("membership/span/{id}", ['middleware' => 'permission:span_manage',  'uses' => "Span@update"]);   // Model: Update
# $app->delete("membership/span/{id}", ['middleware' => 'permission:span_manage',  'uses' => "Span@delete"]);   // Model: Delete

# DONE Entity
# DONE $app->   get("membership/group",       ['middleware' => 'permission:group_view',   'uses' => "Group@list"]);    // Get collection
# DONE $app->  post("membership/group",       ['middleware' => 'permission:group_create', 'uses' => "Group@create"]);  // Model: Create
# DONE $app->   get("membership/group/{id}",  ['middleware' => 'permission:group_view',   'uses' => "Group@read"]);    // Model: Read
# DONE $app->   put("membership/group/{id}",  ['middleware' => 'permission:group_edit',   'uses' => "Group@update"]);  // Model: Update
# DONE $app->delete("membership/group/{id}",  ['middleware' => 'permission:group_delete', 'uses' => "Group@delete"]);  // Model: Delete
# Relation
# $app->   get("membership/group/{id}/members",        ['middleware' => 'permission:group_member_view',   'uses' => "Group@getMembers"]);    // Get collection with members
# $app->  post("membership/group/{id}/members/add",    ['middleware' => 'permission:group_member_add',    'uses' => "Group@addMembers"]);
# $app->  post("membership/group/{id}/members/remove", ['middleware' => 'permission:group_member_remove', 'uses' => "Group@removeMembers"]);
# Relation
# $app->   get("membership/group/{id}/permissions",        ['middleware' => 'permission:permission_view',   'uses' => "Group@listPermissions"]);  // Model: Create
# $app->  post("membership/group/{id}/permissions/add",    ['middleware' => 'permission:permission_manage', 'uses' => "Group@addPermissions"]);  // Model: Create
# $app->  post("membership/group/{id}/permissions/remove", ['middleware' => 'permission:permission_manage', 'uses' => "Group@removePermissions"]);  // Model: Create

# Entity
# $app->   get("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@list"]);     // Get collection
# $app->  post("membership/permission",      ['middleware' => 'permission:permission_manage',  'uses' => "Permission@create"]);   // Model: Create
# $app->   get("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@read"]);     // Model: Read
# $app->   put("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@update"]);   // Model: Update
# $app->delete("membership/permission/{id}", ['middleware' => 'permission:permission_manage',  'uses' => "Permission@delete"]);   // Model: Delete

# IGNORE // Roles
# IGNORE $app->   get("membership/role",        "Role@list");     // Get collection
# IGNORE $app->  post("membership/role",        "Role@create");   // Model: Create
# IGNORE $app->   get("membership/role/{id}",   "Role@read");     // Model: Read
# IGNORE $app->   put("membership/role/{id}",   "Role@update");   // Model: Update
# IGNORE $app->delete("membership/role/{id}",   "Role@delete");   // Model: Delete

# NOT USED $app->  post("membership/authenticate", "Member@authenticate");   // Authenticate a member

