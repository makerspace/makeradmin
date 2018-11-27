import Base from './Base';


export default class Group extends Base {
    
    deleteConfirmMessage() {
        return `Are you sure you want to delete group ${this.title}?`;
    }
    
    canSave() {
        return this.isDirty() && this.title && this.name;
    }
}

Group.model = {
    id: "group_id",
    root: "/membership/group",
    attributes: {
        created_at: null,
        updated_at: null,
        parent: "",
        name: "",
        title: "",
        description: "",
        num_members: 0,
    },
};
