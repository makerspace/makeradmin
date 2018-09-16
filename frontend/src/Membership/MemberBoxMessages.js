import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Message from "../Models/Message";
import DateTime from "../Components/Form/DateTime";


const Row = props => {
    const {item} = props;
    
    return (
        <tr>
            <td>{Message.statusText(item)}</td>
            <td><DateTime date={item.created_at}/></td>
            <td>{Message.typeIcon(item)} {item.recipient}</td>
            <td>{item.subject}</td>
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
            {title: "Status", sort: "status"},
            {title: "Skapad", sort: "created_at"},
            {title: "Mottagare", sort: "recipient"},
            {title: "Rubrik", sort: "subject"},
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}


export default MemberBoxMessages;
