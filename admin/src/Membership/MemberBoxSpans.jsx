import React from 'react';
import {Link} from "react-router";
import Collection from "../Models/Collection";
import Span from "../Models/Span";
import {confirmModal} from "../message";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import DateShow from "../Components/DateShow";
import 'react-day-picker/lib/style.css';
import MembershipPeriodsInput from "./MembershipPeriodsInput";


class MemberBoxSpans extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Span, filter: {member_id: props.params.member_id}, pageSize: 0});
        this.state = {items: []};
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
                <MembershipPeriodsInput spans={this.collection} member_id={this.props.params.member_id}/>
                <h2>Spans</h2>
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        {title: "#", sort: "span_id"},
                        {title: "Typ", sort: "span_type"},
                        {title: "Skapad", sort: "created_at"},
                        {title: ""},
                        {title: "Raderad", sort: "deleted_at"},
                        {title: "Start", sort: "startdate"},
                        {title: "Slut", sort: "enddate"},
                    ]}
                    rowComponent={({item}) => (
                        <tr>
                            <td><Link to={"/membership/spans/" + item.id}>{item.id}</Link></td>
                            <td><Link to={"/membership/spans/" + item.id}>{item.span_type}</Link></td>
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
