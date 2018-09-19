import React from 'react';
import {Link} from "react-router";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import OrderRow from "../Models/OrderRow";
import OrderAction from "../Models/OrderAction";
import Currency from "../Components/Currency";


class OrderShow extends React.Component {

    constructor(props) {
        super(props);
        const {id} = props.params;
        this.order = Order.get(id);
        this.state = {};
        this.orderRows = new Collection({type: OrderRow, url: `/webshop/transaction/${id}/content`, pageSize: 0});
        this.orderActions = new Collection({type: OrderAction, url: `/webshop/transaction/${id}/actions`, pageSize: 0});
    }
    
    componentDidMount() {
        this.unsubscribe = this.order.subscribe(() => {
            const {member_id} = this.order;
            this.setState({member_id});
        });
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {member_id} = this.state;
        const {id} = this.props.params;
        
        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Order #{id}</h2>
                    <div>
                        <h3>Medlem</h3>
                        <Link to={"/membership/members/" + member_id}>member_id {member_id}</Link>
                    </div>
                </div>
                <div className="uk-margin-top">
                    <h3>Orderrader</h3>
                    <CollectionTable
                        emptyMessage="Listan är tom"
                        collection={this.orderRows}
                        columns={[
                            {title: "Produkt"},
                            {title: "Pris", class: 'uk-text-right'},
                            {title: "Antal"},
                            {title: "Summa", class: 'uk-text-right'}
                        ]}
                        rowComponent={({item}) =>
                            <tr>
                                <td><Link to={"/sales/product/" + item.product_id}>{item.product_name}</Link></td>
                                <td className="uk-text-right"><Currency value={100 * item.amount / item.count}/> kr</td>
                                <td>{item.count}</td>
                                <td className="uk-text-right"><Currency value={100 * item.amount} /> kr</td>
                            </tr>
                        }
                    />
                </div>
                <div className="uk-margin-top">
                    <h3>Ordereffekter</h3>
                    <CollectionTable
                        emptyMessage="Listan är tom"
                        collection={this.orderActions}
                        columns={[
                            {title: "Orderrad"},
                            {title: "Åtgärd"},
                            {title: "Antal", class: 'uk-text-right'},
                            {title: "Utförd", class: 'uk-text-right'},
                        ]}
                        rowComponent={({item}) => {
                            return (<tr>
                                <td>{item.content_id}</td>
                                <td>{item.action}</td>
                                <td className="uk-text-right">{item.value}</td>
                                <td className="uk-text-right">{item.completed_at ? item.completed_at : 'pending'}</td>
                            </tr>);
                        }}
                    />
                </div>
            </div>
        );
    }
}

export default OrderShow;
