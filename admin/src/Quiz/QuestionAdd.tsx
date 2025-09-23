import React, { useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import QuizQuestion from "../Models/QuizQuestion";
import QuestionEditForm from "./QuestionEditForm";

interface Props {}

const QuestionAdd: React.FC<Props> = () => {
    const { quiz_id } = useParams<{ quiz_id: string }>();
    const navigate = useNavigate();
    const questionRef = useRef(new QuizQuestion());

    const save = async () => {
        questionRef.current.quiz_id = parseInt(quiz_id!);
        await questionRef.current.save();
        navigate("/quiz/question/" + questionRef.current.id, { replace: true });
    };

    const handleDelete = () => {
        navigate(`/quiz/${quiz_id}`);
    };

    const handleNew = () => {
        navigate(`/quiz/${quiz_id}/question/add`);
    };

    return (
        <QuestionEditForm
            question={questionRef.current}
            onSave={save}
            onDelete={handleDelete}
            onNew={handleNew}
        />
    );
};

export default QuestionAdd;
