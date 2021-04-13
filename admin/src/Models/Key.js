import Base from './Base';


export default class Key extends Base {
    
    deleteConfirmMessage() {
        return `Are you sure you want to delete key ${this.tagid}?`;
    }
    
    canSave() {
        return this.isDirty() && this.tagid.length > 0;
    }
}

Key.model = {
    id: "key_id",
    root: "/membership/key",
    attributes: {
        key_id: 0,
        member_id: null,
        created_at: null,
        updated_at: null,
        description: "",
        tagid: "",
        // extend="member"
        member_number: null,
    },
};
