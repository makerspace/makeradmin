import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import Collection from "../Models/Collection";
import Order from "../Models/Order";
import { Link } from "react-router-dom";
import React from "react";

const Row = (props) => {
    const { item } = props;
    return (
        <tr>
            <td>
                <Link to={"/sales/order/" + item.id}>{item.id}</Link>
            </td>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{item.status}</td>
            <td className="uk-text-right">{item.amount} kr</td>
        </tr>
    );
};

class MemberBoxOrders extends React.Component {
    constructor(props) {
        super(props);
        this.collection = new Collection({
            type: Order,
            url: `/webshop/member/${props.match.params.member_id}/transactions`,
        });
    }

    render() {
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
                    collection={this.collection}
                    columns={columns}
                />
            </div>
        );
    }
}

export default MemberBoxOrders;
