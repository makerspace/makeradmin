import Base from "./Base";

export default class Group extends Base<Group> {
    created_at!: string | null;
    updated_at!: string | null;
    deleted_at!: string | null;
    name!: string;
    title!: string;
    description!: string;
    num_members!: number;

    static model = {
        id: "group_id",
        root: "/membership/group",
        attributes: {
            created_at: null,
            updated_at: null,
            deleted_at: null,
            name: "",
            title: "",
            description: "",
            num_members: 0,
        },
    };

    override deleteConfirmMessage() {
        return `Are you sure you want to delete group ${this.title}?`;
    }

    override canSave() {
        return this.isDirty() && !!this.title && !!this.name;
    }
}
