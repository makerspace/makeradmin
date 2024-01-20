import CollectionTable from "../Components/CollectionTable";
import SearchBox from "../Components/SearchBox";
import TextInput from "../Components/TextInput";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import TransactionCostCenter from "../Models/TransactionCostCenter";
class AccountingCostCenter extends CollectionNavigation {
    constructor(props) {
        super(props);
        this.state = { saveEnabled: false };
        this.transactionCostCenter = new TransactionCostCenter();
        const { search, page } = this.state;
        this.collection = new Collection({
            type: TransactionCostCenter,
            search: search,
            page: page,
        });
    }

    componentDidMount() {
        const transactionCostCenter = this.transactionCostCenter;
        this.unsubscribe = transactionCostCenter.subscribe(() =>
            this.setState({ saveEnabled: transactionCostCenter.canSave() }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    createCostCenter() {
        this.transactionCostCenter.save().then(() => {
            this.transactionCostCenter.reset();
            this.collection.fetch();
        });
    }

    render() {
        const { saveEnabled } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Hantera kostnadsställe</h2>
                    <p>
                        På denna sida kan du lägga till och ta bort
                        kostnadsställen.
                    </p>
                </div>

                <div className="meep">
                    <form
                        className="uk-form uk-margin-bottom"
                        onSubmit={(e) => {
                            e.preventDefault();
                            this.createCostCenter();
                            return false;
                        }}
                    >
                        <TextInput
                            model={this.transactionCostCenter}
                            name="cost_center"
                            title="Namn"
                            placeholder="Namn på nytt kostnadsställe"
                        />
                        <TextInput
                            model={this.transactionCostCenter}
                            name="description"
                            title="Beskrivning"
                            placeholder="Beskrivning av nytt kostnadsställe"
                        />

                        <div className="uk-form-row uk-margin-top">
                            <div className="uk-form-controls">
                                <button
                                    className="uk-button uk-button-success uk-float-right"
                                    disabled={!saveEnabled}
                                >
                                    <i className="uk-icon-save" />{" "}
                                    {this.transactionCostCenter.id
                                        ? "Spara nytt kostnadsställe"
                                        : "Skapa nytt kostnadsställe"}
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
                            { title: "Namn", sort: "cost_center" },
                            { title: "Beskrivning", sort: "description" },
                            { title: "" },
                        ]}
                        rowComponent={({ item, deleteItem }) => (
                            <tr>
                                <td>{item.cost_center}</td>
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

export default AccountingCostCenter;
