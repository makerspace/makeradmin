import Base from './Base';

export default class ProductImage extends Base {
    
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
