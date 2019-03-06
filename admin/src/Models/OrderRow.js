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
        id: 0,
        count: null,
        product_id: null,
        name: "",
    },
};
