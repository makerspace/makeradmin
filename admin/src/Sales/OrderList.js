import React from 'react';
import { Link } from "react-router-dom";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";

class SearchBox extends React.Component {

    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div className="filterbox">
                <div className="uk-grid">
                    <div className="uk-width-2-3">
                        <form className="uk-form">
                            <div className="uk-form-icon">
                                <i className="uk-icon-search"/>
                                <input ref={c => this.search = c} tabIndex="1" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord"
                                       onChange={() => this.props.onChange(this.search.value)} />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/sales/order/" + item.id}>{item.id}</Link></td>
            <td><DateTimeShow date={item.created_at}/></td>
            <td>{item.status}</td>
            <td><Link to={"/membership/members/" + item.member_id}>#{item.member_number}: {item.firstname} {item.lastname}</Link></td>
            <td className='uk-text-right'>{item.amount} kr</td>
        </tr>
    );
};


class OrderList extends React.Component {
    
    constructor(props) {
        super(props);
        this.collection = new Collection({type: Order, url: "/webshop/transaction", expand: 'member'});
    }
    
    render() {
        const columns = [
            {title: "Order"},
            {title: "Skapad"},
            {title: "Status"},
            {title: "Medlem"},
            {title: "Belopp"},
        ];

        return (
            <div className="uk-margin-top">
                <h2>Inkommna ordrar</h2>
                <SearchBox onChange={terms => this.collection.updateSearch(terms)} />
                <CollectionTable emptyMessage="Ingar ordrar" rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default OrderList;
