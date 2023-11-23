import React from 'react';

import TransactionAccountForm from '../Components/TransactionAccountForm';
import { browserHistory } from '../browser_history';
import TransactionAccount from "../Models/TransactionAccount";


class TransactionAccountAdd extends React.Component {

    constructor(props) {
        super(props);
        this.transaction_account = new TransactionAccount();
    }

    render() {
        return (
            <div>
                <h2>Skapa bokföringskonto</h2>
                <TransactionAccountForm
                    transaction_account={this.transaction_account}
                    onSave={() => this.transaction_account.save().then(() => browserHistory.replace('/sales/transaction_accounts/' + this.transaction_account.id))}
                />
            </div>
        );
    }
}

export default TransactionAccountAdd;
