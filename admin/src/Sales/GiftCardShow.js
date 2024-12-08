import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Currency from "../Components/Currency";
import Collection from "../Models/Collection";
import GiftCard from "../Models/GiftCard";
import GiftCardRow from "../Models/GiftCardRow";

const GiftCardShow = ({ match }) => {
    const { id } = match.params;
    const [state, setState] = useState({});

    const gift_card = React.useMemo(() => GiftCard.get(id), [id]);
    const gift_cardRows = React.useMemo(
        () =>
            new Collection({
                type: GiftCardRow,
                url: `/webshop/gift-card/${id}/products`,
                pageSize: 0,
                expand: "product",
            }),
        [id],
    );

    useEffect(() => {
        const unsubscribe = gift_card.subscribe(() => {
            const { email, validation_code } = gift_card;
            setState({ email, validation_code });
        });

        return () => {
            unsubscribe();
        };
    }, [gift_card]);

    const { email, validation_code } = state;

    return (
        <div>
            <div className="uk-margin-top">
                <h2>Presentkort #{id}</h2>
                <div>
                    <h3>Email</h3>
                    <td>{email}</td>
                </div>
                <div>
                    <h3>Valideringskod</h3>
                    <td>{validation_code}</td>
                </div>
            </div>
            <div className="uk-margin-top">
                <h3>Orderrader</h3>
                <CollectionTable
                    emptyMessage="Listan är tom"
                    collection={gift_cardRows}
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
                                    value={
                                        (100 * item.amount) /
                                        item.product_quantity
                                    }
                                />{" "}
                                kr
                            </td>
                            <td>{item.product_quantity}</td>
                            <td className="uk-text-right">
                                <Currency value={100 * item.amount} /> kr
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
};

export default GiftCardShow;
