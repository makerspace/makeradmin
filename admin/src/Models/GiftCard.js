import Base from "./Base";

export default class GiftCard extends Base {
    del() {
        throw new Error("Gift card delete not supported.");
    }
}

GiftCard.model = {
    id: "id",
    root: "/webshop/gift-card",
    attributes: {
        created_at: null,
        email: "",
        status: "",
        amount: 0,
        validation_code: 0,
    },
};
