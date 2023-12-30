import Base from "./Base";

export default class QuizQuestionOption extends Base {
    id: number | null;
    question_id: number;
    description: string;
    answer_description: string;
    correct: boolean;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;

    static model = {
        root: "/quiz/question_options",
        id: "id",
        attributes: {
            question_id: 0,
            correct: false,
            description: "",
            answer_description: "",
        },
    };

    deleteConfirmMessage() {
        return "Are you sure you want to delete this option?";
    }
}
