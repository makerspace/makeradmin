import React, { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { confirmModal } from "../message";
import Quiz from "../Models/Quiz";
import { QuizGraph } from "../Statistics/Graphs/QuizGraph";
import QuestionListRouter from "./QuestionList";
import QuizEditForm from "./QuizEditForm";

const QuizShow: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [quiz, setQuiz] = useState<Quiz>(
        () => Quiz.get(parseInt(id!)) as Quiz,
    );
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        const unsubscribe = quiz.subscribe(() => setLoaded(true));
        return () => {
            unsubscribe();
        };
    }, [quiz]);

    const save = useCallback(() => {
        quiz.save();
    }, [quiz]);

    const handleDelete = useCallback(async () => {
        try {
            await confirmModal(quiz.deleteConfirmMessage());
            await quiz.del();
            navigate("/quiz/");
        } catch {}
    }, [quiz, navigate]);

    const restore = useCallback(async () => {
        quiz.deleted_at = null;
        await quiz.save();
        await quiz.refresh();
    }, [quiz]);

    if (quiz.deleted_at !== null) {
        return (
            <>
                <h1>{quiz.name}</h1>
                <p>Det här quizzet har blivit raderat :(</p>
            </>
        );
    }

    const quiz_id = quiz.id;

    return (
        <>
            <QuizEditForm quiz={quiz} onSave={save} onDelete={handleDelete} />
            {quiz_id != null && (
                <>
                    <QuestionListRouter quiz_id={quiz_id} />
                    <h2>Statistics</h2>
                    <QuizGraph quiz_id={quiz_id} />
                </>
            )}
        </>
    );
};

export default QuizShow;
