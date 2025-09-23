import React from "react";
import QuizAdd from "./QuizAdd";
import QuestionAdd from "./QuestionAdd";
import QuestionShow from "./QuestionShow";
import QuizShow from "./QuizShow";
import QuizList from "./QuizList";

const quizRoutes = [
    {
        path: "",
        element: <QuizList />,
    },
    {
        path: "add",
        element: <QuizAdd />,
    },
    {
        path: ":id",
        element: <QuizShow />,
    },
    {
        path: ":quiz_id/question/add",
        element: <QuestionAdd />,
    },
    {
        path: "question/:id",
        element: <QuestionShow />,
    },
];

export default quizRoutes;
