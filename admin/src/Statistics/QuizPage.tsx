import { useJson } from "Hooks/useJson";
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { QuizGraph } from "./Graphs/QuizGraph";

type Quiz = {
    id: number;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;
};

export default () => {
    const {
        data: quizzes,
        isLoading,
        error,
    } = useJson<Quiz[]>({ url: "/quiz/quiz" });

    const sortedQuizzes = useMemo(() => {
        if (quizzes === null) {
            return null;
        }
        return quizzes.sort((a, b) => a.name.localeCompare(b.name));
    }, [quizzes]);

    return (
        <div className="uk-width-1-1">
            <h2>Quiz Statistics</h2>
            {sortedQuizzes !== null &&
                sortedQuizzes
                    .filter((q) => q.deleted_at === null)
                    .map((quiz) => (
                        <>
                            <h3>
                                <Link
                                    className="uk-link uk-link-text"
                                    to={`/quiz/${quiz.id}`}
                                >
                                    {quiz.name}
                                </Link>
                            </h3>
                            <QuizGraph quiz_id={quiz.id} />
                            <hr />
                        </>
                    ))}
            {isLoading && <div uk-spinner></div>}
        </div>
    );
};
