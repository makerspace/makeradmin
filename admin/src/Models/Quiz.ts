import Base from "./Base";

export default class Quiz extends Base {
    id: number | null;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;

    static model = {
        root: "/quiz/quiz",
        id: "id",
        attributes: {
            name: "",
            description: "",
            deleted_at: null as string,
        },
    };

    deleteConfirmMessage() {
        return "Are you sure you want to delete this quiz?";
    }
}
