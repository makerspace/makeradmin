import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import Collection from "../Models/Collection";
import Order from "../Models/Order";
import OrderAction from "../Models/OrderAction";
import OrderRow from "../Models/OrderRow";
import { dateTimeToStr } from "../utils";

const OrderShow = () => {
    const { id } = useParams(); // Get id from URL params
    const [memberId, setMemberId] = useState(null);

    const order = Order.get(id);
    const orderRows = new Collection({
        type: OrderRow,
        url: `/webshop/transaction/${id}/contents`,
        pageSize: 0,
        expand: "product",
    });
    const orderActions = new Collection({
        type: OrderAction,
        url: `/webshop/transaction/${id}/actions`,
        pageSize: 0,
    });

    useEffect(() => {
        const unsubscribe = order.subscribe(() => {
            const { member_id } = order;
            setMemberId(member_id);
        });

        return () => unsubscribe(); // Cleanup on component unmount
    }, [order]);

    return (
        <div>
            <div className="uk-margin-top">
                <h2>Order #{id}</h2>
                <div>
                    <h3>Medlem</h3>
                    <Link to={`/membership/members/${memberId}`}>
                        member_id {memberId}
                    </Link>
                </div>
            </div>
            <div className="uk-margin-top">
                <h3>Orderrader</h3>
                <CollectionTable
                    emptyMessage="Listan är tom"
                    collection={orderRows}
                    columns={[
                        { title: "Produkt" },
                        { title: "Pris", class: "uk-text-right" },
                        { title: "Antal" },
                        { title: "Summa", class: "uk-text-right" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr key={item.product_id}>
                            <td>
                                <Link to={`/sales/product/${item.product_id}`}>
                                    {item.name}
                                </Link>
                            </td>
                            <td className="uk-text-right">
                                <Currency
                                    value={(100 * item.amount) / item.count}
                                />{" "}
                                kr
                            </td>
                            <td>{item.count}</td>
                            <td className="uk-text-right">
                                <Currency value={100 * item.amount} /> kr
                            </td>
                        </tr>
                    )}
                />
            </div>
            <div className="uk-margin-top">
                <h3>Ordereffekter</h3>
                <CollectionTable
                    emptyMessage="Listan är tom"
                    collection={orderActions}
                    columns={[
                        { title: "Orderrad" },
                        { title: "Åtgärd" },
                        { title: "Antal", class: "uk-text-right" },
                        { title: "Utförd", class: "uk-text-right" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr key={item.id}>
                            <td>{item.id}</td>
                            <td>{item.action_type}</td>
                            <td className="uk-text-right">{item.value}</td>
                            <td className="uk-text-right">
                                {item.completed_at
                                    ? dateTimeToStr(item.completed_at)
                                    : "pending"}
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
};

export default OrderShow;
