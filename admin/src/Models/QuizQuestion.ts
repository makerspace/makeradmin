import Base from "./Base";

export default class QuizQuestion extends Base {
    id: number | null;
    quiz_id: number;
    question: string;
    mode: "single_choice" | "multiple_choice";
    answer_description: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;

    static model = {
        root: "/quiz/question",
        id: "id",
        attributes: {
            question: "",
            answer_description: "",
            quiz_id: -1,
            mode: "single_choice",
        },
    };

    deleteConfirmMessage() {
        return "Are you sure you want to delete this question?";
    }
}
