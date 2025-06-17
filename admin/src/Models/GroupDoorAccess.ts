import Base from "./Base";

export default class GroupDoorAccess extends Base<GroupDoorAccess> {
    group_id!: number;
    accessy_asset_publication_guid!: string;
    created_at!: Date | null;
    updated_at!: Date | null;
    deleted_at!: Date | null;

    static model = {
        root: "/membership/group_door_access_permissions",
        id: "id",
        attributes: {
            accessy_asset_publication_guid: null,
            deleted_at: null,
        },
    };
}
