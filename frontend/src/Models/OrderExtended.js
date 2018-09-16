import Order from './Order';


export default class OrderExtended extends Order {
}

OrderExtended.model = {
    id: "id",
    root: null,
    attributes: Object.assign(
        {},
        Order.model.attributes,
        {
            member_name:   "",
            member_number: 0,
        }
    ),
};
