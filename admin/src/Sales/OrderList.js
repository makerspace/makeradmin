import React from 'react';
import { Link } from "react-router-dom";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";

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
        this.onSearch = this.onSearch.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        this.collection = new Collection({type: Order, url: "/webshop/transaction", expand: 'member', search: search_term});
        this.state = {'search': search_term};
    }

    onSearch(term) {
        this.setState({'search': term});
        this.collection.updateSearch(term);
        if (term === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", term);
        }
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
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
                <SearchBox handleChange={this.onSearch} value={this.state.search}/>
                <CollectionTable emptyMessage="Ingar ordrar" rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default OrderList;
