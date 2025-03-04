import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import useModel from "../Hooks/useModel";
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import Order from "../Models/Order";
import OrderRow from "../Models/OrderRow";
import TransactionAction from "../Models/TransactionAction";
import { dateTimeToStr } from "../utils";

const MemberInfo = ({ id }) => {
    const member = useModel(Member, id);
    return <Link to={`/membership/members/${id}`}>{member.toString()}</Link>;
};

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
    const actions = useMemo(
        () =>
            new Collection({
                type: TransactionAction,
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

    const member_info = memberId && <MemberInfo id={memberId} />;

    let status_badge = null;
    switch (order.status) {
        case "completed":
            status_badge = (
                <span className="uk-badge uk-label-success">Klar</span>
            );
            break;
        case "pending":
            status_badge = (
                <span className="uk-badge uk-label-info">Pågående</span>
            );
            break;
        case "failed":
            status_badge = (
                <span className="uk-badge uk-label-danger">Misslyckades</span>
            );
            break;
        case "":
            break;
        default:
            console.warn("Unhandled order status", order.status);
            status_badge = (
                <span className="uk-badge uk-label-default">
                    Unknown ({order.status})
                </span>
            );
    }

    const date_info = order.created_at && (
        <>({dateTimeToStr(order.created_at)})</>
    );

    return (
        <div>
            <div className="uk-margin-top">
                <h2>
                    Order #{id} {date_info} {status_badge}
                </h2>
                <div>
                    <h3>Medlem</h3>
                    {member_info}
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
                    collection={actions}
                    columns={[
                        { title: "Orderrad" },
                        { title: "Åtgärd" },
                        { title: "Antal", class: "uk-text-right" },
                        { title: "Status" },
                        { title: "Utförd", class: "uk-text-right" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr>
                            <td>{item.id}</td>
                            <td>{item.action_type}</td>
                            <td className="uk-text-right">{item.value}</td>
                            <td>
                                {item.statusEmoji()} {item.status}
                            </td>
                            <td className="uk-text-right">
                                {item.completed_at
                                    ? dateTimeToStr(item.completed_at)
                                    : null}
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
};

export default OrderShow;
