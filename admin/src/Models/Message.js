import React from 'react';
import Base from './Base';


export default class Message extends Base {
    
    del() {
        throw new Error("Message delete not supported.");
    }
    
    canSave() {
        return this.body && this.recipients && this.recipients.length && (this.message_type !== 'email' || this.title);
    }
}

Message.model = {
    id: "messages_message_id",
    root: "/messages/message",
    attributes: {
        body: "",  // TODO Rename to description.
        created_at: null,
        updated_at: null,
        entity_id: 0,
        messages_message_id: 0,
        message_type: "email",
        num_recipients: 0,
        recipient: "",
        recipient_id: 0,
        recipients: [],
        status: "",
        title: "",
        date_sent: null,
    },
};


Message.typeIcon = message => {
    switch (message.message_type) {
        case "email":
            return <i className="uk-icon-envelope" title="E-post"/>;
        case "sms":
            return <i className="uk-icon-commenting" title="SMS"/>;
        default:
            return message.message_type;
    }
};


Message.typeText = message => {
    switch (message.message_type) {
        case "email":
            return "E-post";
        case "sms":
            return "SMS";
        default:
            return message.message_type;
    }
};


Message.statusText = message => {
    switch (message.status) {
        case "queued":
            return "Köad";
        case "failed":
            return "Misslycad";
        case "sent":
            return "Skickad";
        default:
            return "Okänt";
    }
};


