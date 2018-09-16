import Base from './Base';


export default class Permission extends Base {
    
    deleteConfirmMessage() {
        throw new Error("TBD");
        // return `Are you sure you want to delete permission ${this.permission}?`;
    }
    
    canSave() {
        return this.isDirty();
    }
}

Permission.model = {
    id: "permission_id",
    root: "/membership/permission",
    attributes: {
        permission: "",
    },
};
