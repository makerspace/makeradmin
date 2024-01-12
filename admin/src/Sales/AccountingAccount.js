import React from "react";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import CollectionNavigation from "../Models/CollectionNavigation";
import TextInput from "../Components/TextInput";
import TransactionAccount from "../Models/TransactionAccount";
import SearchBox from "../Components/SearchBox";
import Textarea from "../Components/Textarea";

class AccountingAccount extends CollectionNavigation {
    constructor(props) {
        super(props);
        this.state = { saveEnabled: false };
        this.transactionAccount = new TransactionAccount();
        const { search, page } = this.state;
        this.collection = new Collection({
            type: TransactionAccount,
            search: search,
            page: page,
        });
    }

    componentDidMount() {
        const transactionAccount = this.transactionAccount;
        this.unsubscribe = transactionAccount.subscribe(() =>
            this.setState({ saveEnabled: transactionAccount.canSave() }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    createAccount() {
        this.transactionAccount.save().then(() => {
            this.transactionAccount.reset();
            this.collection.fetch();
        });
    }

    render() {
        const { saveEnabled } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Hantera konton</h2>
                    <p>På denna sida kan du lägga till och ta bort konton.</p>
                </div>

                <div className="meep">
                    <form
                        className="uk-form uk-margin-bottom"
                        onSubmit={(e) => {
                            e.preventDefault();
                            this.createAccount();
                            return false;
                        }}
                    >
                        <TextInput
                            model={this.transactionAccount}
                            name="account"
                            title="Namn"
                            placeholder="Nummer på nytt konto"
                        />
                        <Textarea
                            model={this.transactionAccount}
                            name="description"
                            title="Beskrivning"
                            placeholder="Beskrivning av nytt konto"
                        />

                        <div className="uk-form-row uk-margin-top">
                            <div className="uk-form-controls">
                                <button
                                    className="uk-button uk-button-success uk-float-right"
                                    disabled={!saveEnabled}
                                >
                                    <i className="uk-icon-save" />{" "}
                                    {this.transactionAccount.id
                                        ? "Spara nytt konto"
                                        : "Skapa nytt konto"}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>

                <div className="uk-margin-top">
                    <SearchBox handleChange={this.onSearch} />
                    <CollectionTable
                        className="uk-margin-top"
                        collection={this.collection}
                        emptyMessage="Inga konton"
                        columns={[
                            { title: "Namn", sort: "account" },
                            { title: "Beskrivning", sort: "description" },
                            { title: "" },
                        ]}
                        rowComponent={({ item, deleteItem }) => (
                            <tr>
                                <td>{item.account}</td>
                                <td>{item.description}</td>
                                <td>
                                    <a
                                        onClick={() => deleteItem(item)}
                                        className="removebutton"
                                    >
                                        <i className="uk-icon-trash" />
                                    </a>
                                </td>
                            </tr>
                        )}
                        onPageNav={this.onPageNav}
                    />
                </div>
            </div>
        );
    }
}

export default AccountingAccount;
