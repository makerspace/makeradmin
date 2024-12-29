from service.api_definition import (
    GET,
    GROUP_CREATE,
    GROUP_DELETE,
    GROUP_EDIT,
    GROUP_MEMBER_ADD,
    GROUP_MEMBER_REMOVE,
    GROUP_MEMBER_VIEW,
    GROUP_VIEW,
    KEYS_EDIT,
    KEYS_VIEW,
    MEMBER_CREATE,
    MEMBER_DELETE,
    MEMBER_EDIT,
    MEMBER_VIEW,
    PERMISSION_MANAGE,
    PERMISSION_VIEW,
    POST,
    SPAN_MANAGE,
    SPAN_VIEW,
    Arg,
    Enum,
    iso_date,
    natural1,
    non_empty_str,
)
from service.entity import ASC, Entity, ExpandField, OrmManyRelation, OrmSingeRelation, not_empty

from membership import service
from membership.member_auth import get_member_permissions
from membership.member_entity import MemberEntity
from membership.membership import (
    add_membership_days,
    get_access_summary,
    get_members_and_membership,
    get_membership_summary,
)
from membership.models import Group, Key, Member, Permission, Span, group_permission, member_group

member_entity = MemberEntity(
    Member,
    validation=dict(email=not_empty, firstname=not_empty),
    default_sort_column="member_number",
    hidden_columns=("password",),
    search_columns=(
        "firstname",
        "lastname",
        "email",
        "address_street",
        "address_extra",
        "address_zipcode",
        "address_city",
        "phone",
        "civicregno",
        "member_number",
    ),
)

group_entity = Entity(
    Group,
    validation=dict(name=not_empty, title=not_empty),
    default_sort_column="title",
    default_sort_order=ASC,
    search_columns=("name", "title", "description"),
)

permission_entity = Entity(
    Permission,
    default_sort_column="permission",
    default_sort_order=ASC,
    search_columns=("permission", "permission_id"),
)

span_entity = Entity(
    Span,
    search_columns=("member_id",),
    expand_fields={"member": ExpandField(Span.member, [Member.member_number, Member.firstname, Member.lastname])},
)

key_entity = Entity(
    Key,
    search_columns=("description", "tagid"),
    expand_fields={"member": ExpandField(Key.member, [Member.member_number, Member.firstname, Member.lastname])},
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
    relation=OrmManyRelation("groups", Group.members, member_group, "group_id", "member_id"),
    permission_list=GROUP_MEMBER_VIEW,
    permission_add=GROUP_MEMBER_ADD,
    permission_remove=GROUP_MEMBER_REMOVE,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/keys",
    entity=key_entity,
    relation=OrmSingeRelation("keys", "member_id"),
    permission_list=KEYS_VIEW,
)


service.related_entity_routes(
    path="/member/<int:related_entity_id>/spans",
    entity=span_entity,
    relation=OrmSingeRelation("spans", "member_id"),
    permission_list=SPAN_VIEW,
)


@service.route("/member/<int:entity_id>/addMembershipDays", method=POST, permission=SPAN_MANAGE)
def member_add_membership_days(
    entity_id=None,
    type=Arg(Enum(Span.MEMBERSHIP, Span.LABACCESS, Span.SPECIAL_LABACESS)),
    days=Arg(natural1),
    creation_reason=Arg(non_empty_str),
    default_start_date=Arg(iso_date, required=False),
):
    return add_membership_days(entity_id, type, days, creation_reason, default_start_date).as_json()


@service.route("/member/<int:member_id>/pending_actions", method=GET, permission=SPAN_VIEW)
def member_get_pending(member_id):
    from shop.shop_data import pending_actions

    return pending_actions(member_id)


@service.route("/member/<int:entity_id>/membership", method=GET, permission=SPAN_VIEW)
def member_get_membership(entity_id=None):
    return get_membership_summary(entity_id).as_json()


@service.route("/member/<int:entity_id>/access", method=GET, permission=KEYS_VIEW)
def member_get_access(entity_id=None):
    return get_access_summary(entity_id)


@service.route("/member/<int:entity_id>/permissions", method=GET, permission=PERMISSION_VIEW)
def member_get_permissions(entity_id=None):
    return [{"permission_id": i, "permission": p} for i, p in get_member_permissions(entity_id)]


@service.route("/member/all_with_membership", method=GET, permission=MEMBER_VIEW)
def all_with_membership(entity_id=None):
    """
    Used for the CSV export feature in MakerAdmin.
    While technically the frontend could reuqest a list of all members and then query individually if they are members or not,
    that would be several thousand API requests which seems kinda unnecessary.
    It also avoids the need to deal with pagination in the frontend for this operation.
    """
    members, memberships = get_members_and_membership()
    dict_members = []
    for member, membership in zip(members, memberships):
        obj = member_entity.to_obj(member)
        obj["membership"] = membership.as_json()
        dict_members.append(obj)
    return dict_members


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
    relation=OrmManyRelation("members", Member.groups, member_group, "member_id", "group_id"),
    permission_list=GROUP_MEMBER_VIEW,
    permission_add=GROUP_MEMBER_ADD,
    permission_remove=GROUP_MEMBER_REMOVE,
)

service.related_entity_routes(
    path="/group/<int:related_entity_id>/permissions",
    entity=permission_entity,
    relation=OrmManyRelation("permissions", Permission.groups, group_permission, "permission_id", "group_id"),
    permission_list=PERMISSION_VIEW,
    permission_add=PERMISSION_MANAGE,
    permission_remove=PERMISSION_MANAGE,
)

service.entity_routes(
    path="/permission",
    entity=permission_entity,
    permission_list=PERMISSION_VIEW,
    permission_read=PERMISSION_VIEW,
    permission_create=PERMISSION_MANAGE,
    permission_update=PERMISSION_MANAGE,
    permission_delete=PERMISSION_MANAGE,
)


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
