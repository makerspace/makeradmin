DELETE FROM `membership_group_permissions` WHERE permission_id >= 43;

DELETE FROM `membership_permissions` WHERE permission_id >= 43;

DELETE FROM `membership_group_permissions` WHERE permission_id IN
   (SELECT permission_id FROM `membership_permissions` WHERE permission NOT IN
     ('member_view', 'member_create', 'member_edit', 'member_delete', 'group_view', 'group_create',
      'member_edit', 'group_delete', 'group_member_view', 'group_member_add', 'group_member_remove',
      'permission_view', 'permission_manage', 'span_view', 'span_manage', 'keys_view', 'keys_edit',
      'message_send', 'message_view', 'webshop', 'webshop_edit'));

DELETE FROM `membership_permissions` WHERE permission NOT IN
  ('member_view', 'member_create', 'member_edit', 'member_delete', 'group_view', 'group_create',
   'member_edit', 'group_delete', 'group_member_view', 'group_member_add', 'group_member_remove',
   'permission_view', 'permission_manage', 'span_view', 'span_manage', 'keys_view', 'keys_edit',
   'message_send', 'message_view', 'webshop', 'webshop_edit');

ALTER TABLE `membership_permissions` ADD UNIQUE INDEX `membership_permission_index` (`permission`);
