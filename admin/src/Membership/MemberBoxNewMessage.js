import { browserHistory } from "../browser_history";
import MessageForm from "../Components/MessageForm";
import { notifySuccess } from "../message";
import Message from "../Models/Message";
import { withRouter } from "react-router";
import React from "react";
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
