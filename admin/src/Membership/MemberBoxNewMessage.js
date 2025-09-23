import React, { useState } from "react";
import { useParams } from "react-router-dom";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { notifySuccess } from "../message";
import { useNavigate } from "react-router";

const MemberBoxMessages = () => {
    const { member_id } = useParams();
    const navigate = useNavigate();
    const [message] = useState(
        new Message({
            recipients: [{ type: "member", id: member_id }],
        }),
    );

    const onSend = () => {
        message.save().then(() => {
            navigate(`/membership/members/${member_id}/messages`);
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

export default MemberBoxMessages;
