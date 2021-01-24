import React from 'react';
import { Link } from "react-router-dom";
import Collection from "../Models/Collection";
import Span from "../Models/Span";
import {confirmModal} from "../message";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import DateShow from "../Components/DateShow";
import 'react-day-picker/lib/style.css';
import MembershipPeriodsInput from "./MembershipPeriodsInput";
import {get} from '../gateway';


class MemberBoxSpans extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Span, url: `/membership/member/${props.match.params.member_id}/spans`, pageSize: 0});
        this.state = {items: [], pending_actions: {}};
        this.pending_actions = get({url: `/membership/member/${props.match.params.member_id}/pending_actions`}).then((r) => {
            const total_add = r.data.reduce((acc, value) => {
                if (value.action.action === "add_labaccess_days")
                    return acc + value.action.value;
                else
                    return acc;
            }, 0);
            console.log("Got pending lab access days: \n" + total_add);
        });
    }

    componentDidMount() {
        this.unsubscribe = this.collection.subscribe(({items}) => {
            this.setState({items});
        });
    }

    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const deleteItem = item => confirmModal(item.deleteConfirmMessage()).then(() => item.del()).then(() => this.collection.fetch(), () => null);
        
        return (
            <div className="uk-margin-top">
                <h2>Medlemsperioder</h2>
                <MembershipPeriodsInput spans={this.collection} member_id={this.props.match.params.member_id}/>
                <h2>Spans</h2>
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        {title: "#", sort: "span_id"},
                        {title: "Typ", sort: "type"},
                        {title: "Skapad", sort: "created_at"},
                        {title: ""},
                        {title: "Raderad", sort: "deleted_at"},
                        {title: "Start", sort: "startdate"},
                        {title: "Slut", sort: "enddate"},
                    ]}
                    rowComponent={({item}) => (
                        <tr>
                            <td><Link to={"/membership/spans/" + item.id}>{item.id}</Link></td>
                            <td><Link to={"/membership/spans/" + item.id}>{item.type}</Link></td>
                            <td><DateTimeShow date={item.created_at}/></td>
                            <td>{item.creation_reason}</td>
                            <td><DateTimeShow date={item.deleted_at}/></td>
                            <td><DateShow date={item.startdate}/></td>
                            <td><DateShow date={item.enddate}/></td>
                            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}


export default MemberBoxSpans;
