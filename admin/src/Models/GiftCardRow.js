import Base from "./Base";

export default class GiftCardRow extends Base {
    del() {
        throw new Error("GiftCard delete not supported.");
    }
}

GiftCardRow.model = {
    id: "id",
    attributes: {
        amount: null,
        product_quantity: null,
        product_id: null,
        name: "",
    },
};
