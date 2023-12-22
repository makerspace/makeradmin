import React from 'react';
import { Link } from "react-router-dom";
import GiftCard from "../Models/GiftCard";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import GiftCardRow from "../Models/GiftCardRow";
import Currency from "../Components/Currency";

class GiftCardShow extends React.Component {

    constructor(props) {
        super(props);
        const { id } = props.match.params;
        this.gift_card = GiftCard.get(id);
        this.state = {};
        this.gift_cardRows = new Collection({ type: GiftCardRow, url: `/webshop/gift-card/${id}/products`, pageSize: 0, expand: 'product' });
    }

    componentDidMount() {
        this.unsubscribe = this.gift_card.subscribe(() => {
            const { email, validation_code } = this.gift_card;
            this.setState({ email, validation_code });
        });
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const { email, validation_code } = this.state;
        const { id } = this.props.match.params;

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
                        collection={this.gift_cardRows}
                        columns={[
                            { title: "Produkt" },
                            { title: "Pris", class: 'uk-text-right' },
                            { title: "Antal" },
                            { title: "Summa", class: 'uk-text-right' }
                        ]}
                        rowComponent={({ item }) =>
                            <tr>
                                <td><Link to={"/sales/product/" + item.product_id}>{item.name}</Link></td>
                                <td className="uk-text-right"><Currency value={100 * item.amount / item.product_quantity} /> kr</td>
                                <td>{item.product_quantity}</td>
                                <td className="uk-text-right"><Currency value={100 * item.amount} /> kr</td>
                            </tr>
                        }
                    />
                </div>
            </div>
        );
    }
}

export default GiftCardShow;
