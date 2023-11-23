import React from 'react';
import TextInput from "./TextInput";
import { withRouter } from "react-router";


class TransactionAccountForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }

    componentDidMount() {
        const { transaction_account } = this.props;
        this.unsubscribe = transaction_account.subscribe(() => this.setState({ saveDisabled: !transaction_account.canSave() }));
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const { transaction_account, onSave, onDelete } = this.props;
        const { saveDisabled } = this.state;

        return (
            <div className="meep">
                <form className="uk-form uk-margin-bottom" onSubmit={(e) => { e.preventDefault(); onSave(); return false; }}>
                    <TextInput model={transaction_account} name="account" title="Konto" />
                    <TextInput model={transaction_account} name="description" title="Beskrivning" />

                    <div className="uk-form-row uk-margin-top">
                        <div className="uk-form-controls">
                            {transaction_account.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash" /> Ta bort konto</a> : ""}
                            <button className="uk-button uk-button-success uk-float-right" disabled={saveDisabled}><i className="uk-icon-save" /> {transaction_account.id ? 'Spara' : 'Skapa'}</button>
                        </div>
                    </div>
                </form>
            </div>

        );
    }
}


export default withRouter(TransactionAccountForm);