import React from "react";
import { useNavigate } from "react-router-dom";
import Quiz from "../Models/Quiz";
import QuizEditForm from "./QuizEditForm";

const QuizAdd: React.FC = () => {
    const navigate = useNavigate();
    const quizRef = React.useRef(new Quiz());

    const save = async () => {
        await quizRef.current.save();
        navigate(`/quiz/${quizRef.current.id}`, { replace: true });
    };

    const handleDelete = () => {
        navigate("/quiz");
    };

    return (
        <>
            <QuizEditForm
                quiz={quizRef.current}
                onSave={save}
                onDelete={handleDelete}
            />
            <div className="uk-margin-top">
                <h2>Quizfrågor</h2>
                <p className="uk-float-left">
                    Du kan lägga till frågor efter att du har skapat quizet
                </p>
            </div>
        </>
    );
};

export default QuizAdd;
