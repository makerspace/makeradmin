import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import Collection from "../Models/Collection";
import Order from "../Models/Order";
import OrderAction from "../Models/OrderAction";
import OrderRow from "../Models/OrderRow";
import { dateTimeToStr } from "../utils";

const OrderShow = ({ match }) => {
    const { id } = match.params;

    const order = useMemo(() => Order.get(id), [id]);
    const orderRows = useMemo(
        () =>
            new Collection({
                type: OrderRow,
                url: `/webshop/transaction/${id}/contents`,
                pageSize: 0,
                expand: "product",
            }),
        [id],
    );
    const orderActions = useMemo(
        () =>
            new Collection({
                type: OrderAction,
                url: `/webshop/transaction/${id}/actions`,
                pageSize: 0,
            }),
        [id],
    );

    const [memberId, setMemberId] = useState(null);

    useEffect(() => {
        const unsubscribe = order.subscribe(() => {
            const { member_id } = order;
            setMemberId(member_id);
        });

        return () => {
            unsubscribe();
        };
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
                        <tr>
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
                        <tr>
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
