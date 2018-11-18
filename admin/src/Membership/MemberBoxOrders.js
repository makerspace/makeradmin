import React from 'react';
import {Link} from "react-router";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";


const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/sales/order/" + item.id}>{item.id}</Link></td>
            <td><DateTimeShow date={item.created_at}/></td>
            <td>{item.status}</td>
            <td className='uk-text-right'>{item.amount} kr</td>
        </tr>
    );
};


class MemberBoxOrders extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Order, url: "/webshop/transactions_extended_info", filter: {member_id: props.params.member_id}});
    }
    
    render() {
        const columns = [
            {title: "Order"},
            {title: "Skapad"},
            {title: "Status"},
            {title: "Belopp"},
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable emptyMessage="Ingar ordrar" rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default MemberBoxOrders;
