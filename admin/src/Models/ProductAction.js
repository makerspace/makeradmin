import Base from "./Base";

export default class ProductAction extends Base {}

ProductAction.model = {
    id: "id",
    root: "/webshop/product_action",
    attributes: {
        action_type: "",
        product_id: 0,
        value: 0,
    },
};

export const ADD_LABACCESS_DAYS = "add_labaccess_days";
export const ADD_MEMBERSHIP_DAYS = "add_membership_days";
export const ACTION_TYPES = [ADD_LABACCESS_DAYS, ADD_MEMBERSHIP_DAYS];
