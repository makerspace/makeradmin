import React, { useMemo } from "react";
import { withRouter } from "react-router";
import MessageForm from "../Components/MessageForm";
import Message from "../Models/Message";
import { notifySuccess } from "../message";

function MessageAdd(props) {
    const { history } = props;

    // Create a new Message instance
    const message = useMemo(() => new Message(), []);

    // Handler for saving the message
    const onSend = () => {
        message.save().then(() => {
            history.push("/messages");
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

export default withRouter(MessageAdd);
