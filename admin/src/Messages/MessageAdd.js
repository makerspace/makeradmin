import MessageForm from "../Components/MessageForm";
import { notifySuccess } from "../message";
import Message from "../Models/Message";
import { withRouter } from "react-router";
import React from "react";
class MessageAdd extends React.Component {
    constructor(props) {
        super(props);
        this.message = new Message();
    }

    onSend() {
        const { router } = this.props;
        this.message.save().then(() => {
            router.push("/messages");
            notifySuccess("Ditt meddelande har skickats");
        });
    }

    render() {
        return (
            <div className="uk-margin-top">
                <h2>Skapa utskick</h2>
                <MessageForm
                    recipientSelect={true}
                    message={this.message}
                    onSave={() => this.onSend()}
                />
            </div>
        );
    }
}

export default withRouter(MessageAdd);
