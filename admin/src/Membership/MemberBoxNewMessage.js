import React, { useState } from "react";
import { withRouter } from "react-router";
import { useParams } from "react-router-dom";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { browserHistory } from "../browser_history";
import { notifySuccess } from "../message";

const MemberBoxMessages = () => {
    const { member_id } = useParams();
    const [message] = useState(
        new Message({
            recipients: [{ type: "member", id: member_id }],
        }),
    );

    const onSend = () => {
        message.save().then(() => {
            browserHistory.push(`/membership/members/${member_id}/messages`);
            notifySuccess("Ditt meddelande har skickats");
        });
    };

    return (
        <div className="uk-margin-top">
            <MessageForm
                recipientSelect={false}
                message={message}
                onSave={onSend}
            />
        </div>
    );
};

export default withRouter(MemberBoxMessages);
