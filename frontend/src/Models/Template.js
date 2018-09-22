import Base from './Base';


export default class Template extends Base {

    deleteConfirmMessage() {
        return `Are you sure you want to delete template ${this.name}?`;
    }
    
    canSave() {
        return this.isDirty() && this.name;
    }
}

Template.model = {
    id: "template_id",
    root: "/messages/templates",
    attributes: {
        template_id: 0,
        created_at: null,
        updated_at: null,
        name: "",
        title: "",
        description: "",
        deleted_at: null,
        entity_id: 1
    },
};
