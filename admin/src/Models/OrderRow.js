import Base from './Base';


export default class OrderRow extends Base {
    
    del() {
        throw new Error("Order delete not supported.");
    }
}

OrderRow.model = {
    id: "id",
    attributes: {
        amount: null,
        count: null,
        product_id: null,
        transaction_id: null,
        name: "",
    },
};
