import Base from './Base';


export default class QuizQuestion extends Base {
    id: number|null;
    question: string;
    answer_description: string;
    created_at: string;
    updated_at: string;
    deleted_at: string|null;

    static model = {
        root: "/quiz/question",
        id: "id",
        attributes: {
            question: "",
            answer_description: "",
        },
    };

    deleteConfirmMessage() {
        return "Are you sure you want to delete this question?"
    }
}
