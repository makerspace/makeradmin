import React from 'react';
import {Link} from "react-router";
import OrderExtended from "../Models/OrderExtended";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";


// TODO Change to use Order and don't show member link.
const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/sales/order/" + item.id}>{item.id}</Link></td>
            <td>{item.created_at}</td>
            <td>{item.status}</td>
            <td><Link to={"/membership/membersx/" + item.member_id}>{item.member_number}: {item.member_name}</Link></td>
            <td>{item.amount}</td>
        </tr>
    );
};


class MemberBoxOrders extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: OrderExtended, url: "/webshop/transactions_extended_info", filter: {member_id: props.params.member_id}});
    }
    
    render() {
        const columns = [
            {title: "Order"},
            {title: "Datum"},
            {title: "Status"},
            {title: "Medlem"},
            {title: "Belopp"},
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default MemberBoxOrders;
