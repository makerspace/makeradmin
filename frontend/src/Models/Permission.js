import Base from './Base';


export default class Permission extends Base {
    
    deleteConfirmMessage() {
        throw new Error("Order delete not supported.");
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
