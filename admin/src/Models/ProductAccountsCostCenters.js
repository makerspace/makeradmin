import Base from './Base';

export default class ProductAccountsCostCenters extends Base {
}

ProductAccountsCostCenters.model = {
    id: "id",
    root: "/webshop/accounting",
    attributes: {
        product_id: null,
        account_id: null,
        cost_center_id: null,
        debits: null,
        credits: null,
    },
};
