import React from 'react';
import { Link } from 'react-router-dom';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import TransactionAccount from "../Models/TransactionAccount";
import SearchBox from "../Components/SearchBox";
import CollectionNavigation from "../Models/CollectionNavigation";

const Row = props => {
    const { item, deleteItem } = props;

    return (
        < tr >
            <td><Link to={"/sales/transaction_accounts/" + item.id}>{item.account}</Link></td>
            <td><Link to={"/sales/transaction_accounts/" + item.id}>{item.description}</Link></td>
            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash" /></a></td>
        </tr >
    );
};


class TransactionAccountList extends CollectionNavigation {

    constructor(props) {
        super(props);
        const { search, page } = this.state;

        this.collection = new Collection({ type: TransactionAccount, search: search, page: page });
    }

    render() {
        const columns = [
            { title: "Konto", sort: "title" },
            { title: "Beskrivning", sort: "name" },
            { title: "" },
        ];

        return (
            <div>
                <h2>Konton</h2>

                <p className="uk-float-left">På denna sida ser du en lista på samtliga bokföringskonton..</p>
                <Link to="/sales/transaction_accounts/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle" /> Skapa nytt bokföringskonto</Link>

                <SearchBox handleChange={this.onSearch} value={this.state.search} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}

export default TransactionAccountList;
