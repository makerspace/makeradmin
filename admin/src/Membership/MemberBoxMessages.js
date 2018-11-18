import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Message from "../Models/Message";
import DateTimeShow from "../Components/DateTimeShow";
import {Link} from "react-router";


const Row = props => {
    const {item} = props;
    
    return (
        <tr>
            <td><DateTimeShow date={item.created_at}/></td>
            <td>{Message.statusText(item)}</td>
            <td>{Message.typeIcon(item)} {item.recipient}</td>
            <td><Link to={"/messages/" + item.id}>{item.subject}</Link></td>
        </tr>
    );
};


class MemberBoxMessages extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Message, url: "/messages/user/" + props.params.member_id});
    }

    render() {
        const columns = [
            {title: "Skapad", sort: "created_at"},
            {title: "Status", sort: "status"},
            {title: "Mottagare", sort: "recipient"},
            {title: "Meddelande", sort: "subject"},
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
                <Link to={"/membership/members/" + this.props.params.member_id + "/messages/new"} className="uk-button uk-button-primary"><i className="uk-icon-envelope" /> Skicka meddelande</Link>
            </div>
        
        );
    }
}


export default MemberBoxMessages;
