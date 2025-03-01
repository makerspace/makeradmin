import Base from "./Base";

export default class ProductAction extends Base<ProductAction> {
    action_type!: ActionTypes;
    product_id!: number;
    value!: number;

    static model = {
        root: "/webshop/product_action",
        id: "id",
        attributes: {
            name: "",
            description: "",
            deleted_at: null,
        },
    };
}

// Remove when all files are converted to TypeScript: https://github.com/makerspace/makeradmin/issues/605
export const ADD_LABACCESS_DAYS = "add_labaccess_days";
export const ADD_MEMBERSHIP_DAYS = "add_membership_days";
export const ACTION_TYPES = [ADD_LABACCESS_DAYS, ADD_MEMBERSHIP_DAYS];

export enum ActionTypes {
    ADD_LABACCESS_DAYS = "add_labaccess_days",
    ADD_MEMBERSHIP_DAYS = "add_membership_days",
}
