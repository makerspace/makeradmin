import React from 'react';
import PropTypes from 'prop-types';
import TransactionAccount from "../Models/TransactionAccount";
import TransactionAccountForm from "../Components/TransactionAccountForm";
import { confirmModal } from "../message";
import { withRouter } from "react-router";

class TransactionAccountBoxEditInfo extends React.Component {

    render() {
        const { router } = this.props;

        return (
            <div className='uk-margin-top'>
                <TransactionAccountForm
                    transaction_account={this.context.transaction_account}
                    onSave={() => this.context.transaction_account.save()}
                    onDelete={() => {
                        const { transaction_account } = this.context;
                        return confirmModal(transaction_account.deleteConfirmMessage())
                            .then(() => transaction_account.del())
                            .then(() => {
                                router.push("/sales/transaction_accounts/");
                            })
                            .catch(() => null);
                    }}
                />
            </div>
        );
    }
}

TransactionAccountBoxEditInfo.contextTypes = {
    transaction_account: PropTypes.instanceOf(TransactionAccount)
};


export default withRouter(TransactionAccountBoxEditInfo);