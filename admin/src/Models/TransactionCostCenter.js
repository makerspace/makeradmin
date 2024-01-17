import Base from "./Base";

export default class TransactionCostCenter extends Base {
    deleteConfirmMessage() {
        return `Are you sure you want to delete account ${this.cost_center}?`;
    }

    canSave() {
        return this.isDirty() && this.cost_center;
    }
}

TransactionCostCenter.model = {
    id: "id",
    root: "/webshop/transaction_cost_center",
    attributes: {
        created_at: null,
        updated_at: null,
        cost_center: "",
        description: "",
    },
};
