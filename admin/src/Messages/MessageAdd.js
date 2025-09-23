import React, { useMemo } from "react";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { notifySuccess } from "../message";
import { useNavigate } from "react-router";

function MessageAdd() {
    const navigate = useNavigate();

    const message = useMemo(() => new Message(), []);

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

export default MessageAdd;
