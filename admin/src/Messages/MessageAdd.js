import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { notifySuccess } from "../message";

export default function MessageAdd() {
    const [message] = useState(new Message());
    const navigate = useHistory();

    const onSend = () => {
        message.save().then(() => {
            navigate("/messages");
            notifySuccess("Ditt meddelande har skickats");
        });
    };

    return (
        <div className="uk-margin-top">
            <h2>Skapa utskick</h2>
            <MessageForm
                recipientSelect={true}
                message={message}
                onSave={onSend}
            />
        </div>
    );
}
