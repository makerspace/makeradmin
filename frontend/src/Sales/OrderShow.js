import React from 'react';
import {Link} from "react-router";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTime from "../Components/Form/DateTime";
import OrderRow from "../Models/OrderRow";
import OrderAction from "../Models/OrderAction";


const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/sales/order/" + item.id}>{item.id}</Link></td>
            <td><DateTime date={item.created_at}/></td>
            <td>{item.status}</td>
            <td><Link to={"/membership/members/" + item.member_id}>#{item.member_number}: {item.member_name}</Link></td>
            <td className='uk-text-right'>{item.amount} kr</td>
        </tr>
    );
};


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
                        collection={this.orderRows}
                        columns={[
                            {title: "Rad"},
                            {title: "Produkt"},
                            {title: "Pris"},
                            {title: "Antal"},
                            {title: "Summa"},
                        ]}
                        rowComponent={(item) =>
                            "hej"
                        }
                    />
                </div>
                <div className="uk-margin-top">
                    <h3>Ordereffekter</h3>
                    <CollectionTable
                        collection={this.orderActions}
                        columns={[
                            {title: "Rad"},
                            {title: "Orderrad"},
                            {title: "Åtgärd"},
                            {title: "Antal"},
                            {title: "Utförd"},
                        ]}
                        rowComponent={(item) =>
                            "hej"
                        }
                    />
                </div>
            </div>
        );
    }
}

export default OrderShow;
