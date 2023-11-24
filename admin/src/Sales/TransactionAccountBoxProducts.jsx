import React from 'react';
import { Link } from "react-router-dom";
import { Async } from "react-select";
import Collection from "../Models/Collection";
import Product from "../Models/Product";
import CollectionTable from "../Components/CollectionTable";
import { get } from "../gateway";
import * as _ from "underscore";


const Row = collection => props => {
    const { item } = props;
    return (
        <tr>
            <td><Link to={"/sales/product/" + item.id}>{item.name}</Link></td>
            <td>{item.description}</td>
            <td><a onClick={() => collection.remove(item)} className="removebutton"><i className="uk-icon-trash" /></a></td>
        </tr>
    );
};


class TransactionAccountBoxProducts extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({ type: Product, url: `/sales/transaction_account/${props.match.params.transaction_account_id}/products`, idListName: 'products' });
        this.state = { selectedOption: null };
    }

    loadOptions(inputValue, callback) {
        get({ url: '/webshop/product', params: { search: inputValue, sort_by: "name", sort_order: "asc" } }).then(data => callback(data.data));
    }

    selectOption(product) {
        this.setState({ selectedOption: product });

        if (_.isEmpty(product)) {
            return;
        }

        this.collection.add(new Product(product)).then(this.setState({ selectedOption: null }));
    }

    render() {
        const columns = [ //TODO add debit credit column
            { title: "Namn", sort: "name" },
            { title: "Beskrivning", sort: "description" },
            { title: "" },
        ];

        const { selectedOption } = this.state;

        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="product">
                        Lägg till i konto
                    </label>
                    <div className="uk-form-controls">
                        <Async
                            name="product"
                            tabIndex={1}
                            placeholder="Type to search for product"
                            value={selectedOption}
                            getOptionValue={p => p.id}
                            getOptionLabel={p => p.name} //TODO category
                            loadOptions={(v, c) => this.loadOptions(v, c)}
                            onChange={product => this.selectOption(product)}
                        />
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable emptyMessage="Inga produkter för konto" rowComponent={Row(this.collection)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}

export default TransactionAccountBoxProducts;
