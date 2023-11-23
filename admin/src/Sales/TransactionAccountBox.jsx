import React from 'react';
import { withRouter } from 'react-router';
import { NavItem } from "../nav";
import PropTypes from 'prop-types';
import TransactionAccount from "../Models/TransactionAccount";


class TransactionAccountBox extends React.Component {

    constructor(props) {
        super(props);
        const { transaction_account_id } = props.match.params;
        this.transaction_account = TransactionAccount.get(transaction_account_id);
        this.state = { transaction_account_id, title: "" };
    }

    getChildContext() {
        return { transaction_account: this.transaction_account };
    }

    componentDidMount() {
        const transaction_account = this.transaction_account;
        this.unsubscribe = transaction_account.subscribe(() => this.setState({ title: transaction_account.title }));
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const { transaction_account_id } = this.props.match.params;
        const { title } = this.state;

        return (
            <div>
                <h2>Konto {title}</h2>

                <ul className="uk-tab">
                    <NavItem icon={null} to={"/sales/transaction_accounts/" + transaction_account_id + "/info"}>Information</NavItem>
                    <NavItem icon={null} to={"/sales/transaction_accounts/" + transaction_account_id + "/products"}>Produkter</NavItem>
                </ul>
                {this.props.children}
            </div>
        );
    }
}

TransactionAccountBox.childContextTypes = {
    transaction_account: PropTypes.instanceOf(TransactionAccount)
};

export default withRouter(TransactionAccountBox);
