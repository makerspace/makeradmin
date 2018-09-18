import Base from './Base';


export default class OrderAction extends Base {
    
    del() {
        throw new Error("Order delete not supported.");
    }
}

OrderAction.model = {
    id: "action_id",
    attributes: {
        action: "",
        action_id: 0,
        completed_at: null,
        content_id: 0,
        status: "",
        value: null,
    },
};
