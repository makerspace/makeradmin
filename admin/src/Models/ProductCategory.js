import Base from "./Base";

export default class Category extends Base {
    canSave() {
        return this.isDirty() && this.name.length;
    }

    deleteConfirmMessage() {
        return `Are you sure you want to delete category ${this.name}?`;
    }
}

Category.model = {
    id: "id",
    root: "/webshop/category",
    attributes: {
        created_at: null,
        updated_at: null,
        name: "",
    },
};
