import React from 'react';
import { Link } from "react-router-dom";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";
import CollectionNavigation from "../Models/CollectionNavigation";

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


class OrderList extends CollectionNavigation {

    constructor(props) {
        super(props);
        const {search, page} = this.state;

        this.collection = new Collection({type: Order, url: "/webshop/transaction", expand: 'member', search, page});
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
                <CollectionTable emptyMessage="Ingar ordrar" rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}


export default OrderList;
