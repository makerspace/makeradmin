import Base from './Base';

export default class ProductImage extends Base {

    deleteConfirmMessage() {
        return `Are you sure you want to delete image ${this.name}?`;
    }
    
    canSave() {
        return this.isDirty() && this.name.length > 0 && this.data.length > 0;
    }
}

ProductImage.model = {
    id: "id",
    root: "/webshop/product_image",
    attributes: {
        created_at: null,
        updated_at: null,
        name: "",
        type: null,
        data: null,
    },
};
