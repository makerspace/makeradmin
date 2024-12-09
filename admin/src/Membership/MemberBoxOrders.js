import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import Collection from "../Models/Collection";
import Order from "../Models/Order";

const Row = ({ item }) => {
    return (
        <tr>
            <td>
                <Link to={`/sales/order/${item.id}`}>{item.id}</Link>
            </td>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{item.status}</td>
            <td className="uk-text-right">{item.amount} kr</td>
        </tr>
    );
};

function MemberBoxOrders(props) {
    const member_id = props.match.params.member_id;
    const collection = new Collection({
        type: Order,
        url: `/webshop/member/${member_id}/transactions`,
    });

    const columns = [
        { title: "Order" },
        { title: "Skapad" },
        { title: "Status" },
        { title: "Belopp" },
    ];

    return (
        <div className="uk-margin-top">
            <CollectionTable
                emptyMessage="Ingar ordrar"
                rowComponent={Row}
                collection={collection}
                columns={columns}
            />
        </div>
    );
}

export default MemberBoxOrders;
