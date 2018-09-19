import Base from './Base';


export default class Product extends Base {
     deleteConfirmMessage() {
        return `Are you sure you want to product ${this.name}?`;
    }
}

Product.model = {
    id: "id",
    root: "/webshop/product",
    attributes: {
        created_at: null,
        updated_at: null,
        name: "",
        description: "",
        category_id: 0,
        price: 0,
        unit: "",
        smallest_multiple: 1,
    },
};
