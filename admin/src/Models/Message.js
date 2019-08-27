import Base from './Base';


export default class Message extends Base {
    
    del() {
        throw new Error("Message delete not supported.");
    }
    
    canSave() {
        return this.body && this.recipients && this.recipients.length && this.subject;
    }
}

Message.model = {
    id: "id",
    root: "/messages/message",
    attributes: {
        subject: "",
        body: "",
        status: "",
        template: "",
        recipient: "",
        recipients: [],
        created_at: null,
        updated_at: null,
        sent_at: null,
        recipient_id: 0,
    },
};


Message.statusText = message => {
    switch (message.status) {
        case "queued":
            return "Queued";
        case "failed":
            return "Failed";
        case "sent":
            return "Sent";
        default:
            return "Unknown";
    }
};


