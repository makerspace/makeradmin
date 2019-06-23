import React from 'react';
import {withRouter} from "react-router";
import Message from "../Models/Message";
import DateTimeShow from "../Components/DateTimeShow";


class MessageShow extends React.Component {
    
    constructor(props) {
        super(props);
        const {id} = props.params;
        this.message = Message.get(id);
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
                    <table>
                        <tbody>
                        <tr><th align="left">Created</th><td><DateTimeShow date={message.created_at}/></td></tr>
                        <tr><th align="left">Status</th><td>{Message.statusText(message)}</td></tr>
                        <tr><th align="left">Sent</th><td><DateTimeShow date={message.sent_at}/></td></tr>
                        <tr><th align="left">Recipient</th><td>{message.recipient}</td></tr>
                        <tr><th align="left">Template Used</th><td>{message.template}</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <div className="uk-panel uk-panel-box uk-margin-bottom">
                    <h3 className="uk-panel-title" dangerouslySetInnerHTML={{__html: message.subject}}/>
                </div>
                <div className="uk-panel uk-panel-box uk-margin-bottom">
                    <div dangerouslySetInnerHTML={{__html: message.body}}/>
                </div>
            </div>
        );
    }
}
    
export default withRouter(MessageShow);
