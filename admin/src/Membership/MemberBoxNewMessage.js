import React from "react";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { notifySuccess } from "../message";
import { withRouter } from "react-router";
import { browserHistory } from "../browser_history";

class MemberBoxMessages extends React.Component {
    constructor(props) {
        super(props);
        this.message = new Message({
            recipients: [{ type: "member", id: props.match.params.member_id }],
        });
    }

    onSend() {
        const params = this.props.match.params;
        this.message.save().then(() => {
            browserHistory.push(
                "/membership/members/" + params.member_id + "/messages",
            );
            notifySuccess("Ditt meddelande har skickats");
        });
    }

    render() {
        return (
            <div className="uk-margin-top">
                <MessageForm
                    recipientSelect={false}
                    message={this.message}
                    onSave={() => this.onSend()}
                />
            </div>
        );
    }
}

export default withRouter(MemberBoxMessages);
