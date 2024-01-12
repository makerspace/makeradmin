import Base from "./Base";

export default class TransactionAccount extends Base {
    deleteConfirmMessage() {
        return `Are you sure you want to delete account ${this.account}?`;
    }

    canSave() {
        return this.isDirty() && this.account;
    }
}

TransactionAccount.model = {
    id: "id",
    root: "/webshop/transaction_account",
    attributes: {
        created_at: null,
        updated_at: null,
        account: "",
        description: "",
    },
};
