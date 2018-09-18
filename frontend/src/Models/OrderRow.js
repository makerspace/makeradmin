import Base from './Base';


export default class OrderRow extends Base {
    
    del() {
        throw new Error("Order delete not supported.");
    }
}

OrderRow.model = {
    id: "content_id",
    attributes: {
        amount: null,
        content_id: 0,
        count: null,
        product_id: null,
        product_name: "",
    },
};
