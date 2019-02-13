import Base from './Base';


export default class ProductAction extends Base {
}

ProductAction.model = {
    id: "id",
    root: "/webshop/product_action",
    attributes: {
        action_id: 0,
        product_id: 0,
        value: 0,
    },
};
