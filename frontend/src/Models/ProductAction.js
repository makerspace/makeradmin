import Base from './Base';


export default class ProductAction extends Base {
}

ProductAction.model = {
    id: "id",
    attributes: {
        action_id: 0,
        product_id: 0,
        value: 0,
    },
};
