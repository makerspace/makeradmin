import React from 'react';
import { Link } from "react-router-dom";
import Order from "../Models/Order";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";

class SearchBox extends React.Component {

    render() {
        return (
            <div className="filterbox">
                <div className="uk-grid">
                    <div className="uk-width-2-3">
                        <form className="uk-form">
                            <div className="uk-form-icon">
                                <i className="uk-icon-search"/>
                                <input value={this.props.value} ref={c => this.search = c} tabIndex="1" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord" onChange={(e) => this.props.handleChange(e.target.value)} />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/sales/order/" + item.id}>{item.id}</Link></td>
            <td><DateTimeShow date={item.created_at}/></td>
            <td>{item.status}</td>
            <td><Link to={"/membership/members/" + item.member_id}>#{item.member_number}: {item.firstname} {item.lastname}</Link></td>
            <td className='uk-text-right'>{item.amount} kr</td>
        </tr>
    );
};


class OrderList extends React.Component {

    componentDidMount() {
        const params = new URLSearchParams(this.props.location.search);
        const search_term = params.get('search');
        this.setState({'search': search_term});
        this.collection.updateSearch(search_term);
    }

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Order, url: "/webshop/transaction", expand: 'member'});
        this.state = {'search': ''};
        this.onSearch = this.onSearch.bind(this);
    }

    onSearch(term) {
        this.setState({'search': term});
        this.collection.updateSearch(term);
        this.props.history.replace("/sales?search=" + term);
    }

    render() {
        const columns = [
            {title: "Order"},
            {title: "Skapad"},
            {title: "Status"},
            {title: "Medlem"},
            {title: "Belopp"},
        ];

        return (
            <div className="uk-margin-top">
                <h2>Inkommna ordrar</h2>
                <SearchBox handleChange={this.onSearch} value={this.state.search}/>
                <CollectionTable emptyMessage="Ingar ordrar" rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default OrderList;
