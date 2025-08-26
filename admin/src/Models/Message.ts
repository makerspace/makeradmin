import Base from "./Base";

export type MessageRecipient = {
    id: number;
    type: "member" | "group";
};

export default class Message extends Base<Message> {
    subject!: string;
    body!: string;
    status!: string;
    template!: string;
    recipient!: string;
    recipients!: MessageRecipient[];
    created_at!: string | null;
    updated_at!: string | null;
    sent_at!: string | null;
    member_id!: number;

    static model = {
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
            member_id: 0,
        },
    };

    override del(): Promise<void> {
        throw new Error("Message delete not supported.");
    }

    override canSave(): boolean {
        return (
            !!this.body &&
            !!this.recipients &&
            this.recipients.length > 0 &&
            !!this.subject
        );
    }

    static statusText(message: Message): string {
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
    }
}
