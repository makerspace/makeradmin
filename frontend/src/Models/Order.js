import Base from './Base';


export default class Order extends Base {
    
    del() {
        throw new Error("Order delete not supported.");
    }
}

Order.model = {
    id: "id",
    root: "/webshop/transaction",
    attributes: {
        amount: 0,
        created_at: null,
        member_id: 0,
        status: "",
        // extend="member"
        member_number: 0,
        member_name: "",
    },
};
