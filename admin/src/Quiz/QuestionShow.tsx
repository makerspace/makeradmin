import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import QuizQuestion from "../Models/QuizQuestion";
import { confirmModal } from "../message";
import QuestionEditForm from "./QuestionEditForm";

const QuestionShow: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [question, setQuestion] = useState<QuizQuestion | null>(null);
    const questionRef = useRef<QuizQuestion | null>(null);

    useEffect(() => {
        if (!id) return;
        const q = QuizQuestion.get(parseInt(id)) as QuizQuestion;
        questionRef.current = q;
        setQuestion(q);

        const unsubscribe = q.subscribe(() => setQuestion(q));
        return () => {
            unsubscribe();
        };
    }, [id]);

    const save = useCallback(() => {
        questionRef.current?.save();
    }, []);

    const handleDelete = useCallback(async () => {
        if (!questionRef.current) return;
        try {
            await confirmModal(questionRef.current.deleteConfirmMessage());
            await questionRef.current.del();
            navigate(`/quiz/${questionRef.current.quiz_id}`);
        } catch {}
    }, [navigate]);

    const handleNew = useCallback(() => {
        if (!questionRef.current) return;
        navigate(`/quiz/${questionRef.current.quiz_id}/question/add`);
    }, [navigate]);

    return (
        <QuestionEditForm
            question={question}
            onSave={save}
            onDelete={handleDelete}
            onNew={handleNew}
        />
    );
};

export default QuestionShow;
