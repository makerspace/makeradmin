import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Message from "../Models/Message";
import DateTime from "../Components/Form/DateTime";
import {Link} from "react-router";


class MessageList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Message});
    }

    render() {
        return (
            <div className="uk-margin-top">
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        {title: "Skapad", sort: "created_at"},
                        {title: "Status", sort: "status"},
                        {title: "Typ", sort: "type"},
                        {title: "Mottagare"},
                        {title: "Meddelande", sort: "subject"},
                    ]}
                    rowComponent={({item}) => (
                        <tr>
                            <td><DateTime date={item.created_at}/></td>
                            <td>{Message.statusText(item)}</td>
                            <td>{Message.typeIcon(item)}</td>
                            <td>{item.num_recipients} st</td>
                            <td><Link to={"/messages/" + item.id}>{item.subject}</Link></td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}


export default MessageList;
