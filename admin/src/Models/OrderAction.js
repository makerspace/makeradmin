import Base from "./Base";

export default class OrderAction extends Base {
    del() {
        throw new Error("Order delete not supported.");
    }
}

OrderAction.model = {
    id: "id",
    attributes: {
        action_type: "",
        completed_at: null,
        content_id: 0,
        status: "",
        value: null,
        // Action expand.
        name: "",
    },
};
