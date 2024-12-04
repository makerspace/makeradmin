import React, { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import GiftCard from "../Models/GiftCard";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import GiftCardRow from "../Models/GiftCardRow";
import Currency from "../Components/Currency";

const GiftCardShow = () => {
    const { id } = useParams(); // Get id from URL params
    const [giftCardDetails, setGiftCardDetails] = useState({ email: '', validation_code: '' });

    const gift_card = GiftCard.get(id);
    const gift_cardRows = new Collection({
        type: GiftCardRow,
        url: `/webshop/gift-card/${id}/products`,
        pageSize: 0,
        expand: "product",
    });

    useEffect(() => {
        const unsubscribe = gift_card.subscribe(() => {
            const { email, validation_code } = gift_card;
            setGiftCardDetails({ email, validation_code });
        });

        return () => unsubscribe(); // Cleanup on component unmount
    }, [gift_card]);

    const { email, validation_code } = giftCardDetails;

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
                        <tr key={item.product_id}>
                            <td>
                                <Link to={`/sales/product/${item.product_id}`}>
                                    {item.name}
                                </Link>
                            </td>
                            <td className="uk-text-right">
                                <Currency
                                    value={(100 * item.amount) / item.product_quantity}
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
