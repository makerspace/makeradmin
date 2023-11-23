import Base from './Base';

export default class TransactionAccount extends Base {

    canSave() {
        return this.isDirty() && this.account.length && this.description.length; //TODO check that it is an integer
    }

    deleteConfirmMessage() {
        return `Are you sure you want to delete transaction account ${this.account}?`;
    }
}


TransactionAccount.model = {
    id: "id",
    root: "/webshop/transaction_account",
    attributes: {
        created_at: null,
        updated_at: null,
        description: "",
        account: 0,
    },
};
