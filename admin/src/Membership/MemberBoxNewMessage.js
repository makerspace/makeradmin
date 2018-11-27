import React from 'react';
import MessageForm from '../Components/MessageForm';
import Message from "../Models/Message";
import { notifySuccess } from "../message";
import {withRouter} from "react-router";

class MemberBoxMessages extends React.Component {

    constructor(props) {
        super(props);
        this.message = new Message({recipients: [{type: "member", id: props.params.member_id}]});
    }
    
    onSend() {
        const {router, params} = this.props;
        this.message.save().then(() => {
            router.push("/membership/members/" + params.member_id + "/messages");
            notifySuccess("Ditt meddelande har skickats");
        });
    }
    
    render() {
        return (
            <div className="uk-margin-top">
                <MessageForm recipientSelect={false} message={this.message} onSave={() => this.onSend()}/>
            </div>
        );
    }
}

export default withRouter(MemberBoxMessages);
