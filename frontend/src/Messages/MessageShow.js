import React from 'react';
import {Link, withRouter} from "react-router";
import Message from "../Models/Message";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";


class MessageShow extends React.Component {
    
    constructor(props) {
        super(props);
        const {id} = props.params;
        this.message = Message.get(id);
        this.recipients = new Collection({type: Message, url: "/messages/" + id + "/recipients"});
        this.state = {message: {}};
    }
    
    componentDidMount() {
        this.unsubscribe = this.message.subscribe(() => this.setState({message: this.message}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {message} = this.state;
        return (
            <div className="uk-margin-top">
                <h2>Utskick</h2>
                <div className="uk-panel uk-panel-box uk-margin-bottom">
                    <dl>
                        <dt>Skapad</dt><dd><DateTimeShow date={message.created_at}/></dd>
                        <dt>Typ</dt><dd>{Message.typeIcon(message)} {Message.typeText(message)}</dd>
                        <dt>Status</dt><dd>{Message.statusText(message)}</dd>
                        <dt>Antal mottagare</dt><dd>{message.num_recipients}</dd>
                    </dl>
                </div>
                
                <div className="uk-panel uk-panel-box uk-margin-bottom">
                    {
                        message.message_type !== "sms"
                        ?
                        <h3 className="uk-panel-title">{message.subject}</h3>
                        :
                        null
                    }
                    {message.body}
                </div>
                <CollectionTable
                    collection = {this.recipients}
                    columns = {[
                            {title: "Mottagare", sort: "recipient"},
                            {title: "Status"},
                            {title: "Skapad", sort: "created_at"},
                            {title: "Skickad", sort: "date_sent"},
                    ]}
                    rowComponent = {({item}) => (
                            <tr>
                                <td><Link to={"/membership/members/" + item.recipient_id}>{item.recipient}</Link></td>
                                <td>{Message.statusText(item)}</td>
                                <td><DateTimeShow date={item.created_at}/></td>
                                <td><DateTimeShow date={item.date_sent}/></td>
                            </tr>
                    )}
                />
            </div>
        );
    }
}
    
export default withRouter(MessageShow);
