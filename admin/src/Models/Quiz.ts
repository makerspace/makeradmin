import Base from "./Base";

export default class Quiz extends Base<Quiz> {
    name!: string;
    description!: string;
    required_pass_rate!: number;
    send_help_notifications!: boolean;
    visible!: boolean;
    created_at!: string;
    updated_at!: string;
    deleted_at!: string | null;

    static model = {
        root: "/quiz/quiz",
        id: "id",
        attributes: {
            name: "",
            description: "",
            required_pass_rate: 0,
            send_help_notifications: true,
            visible: true,
            deleted_at: null,
        },
    };

    override deleteConfirmMessage() {
        return "Are you sure you want to delete this quiz?";
    }
}
