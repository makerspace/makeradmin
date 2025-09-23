import React from "react";
import MessageAdd from "./MessageAdd";
import MessageList from "./MessageList";
import MessageShow from "./MessageShow";
import { Navigate } from "react-router-dom";

export default [
    {
        index: true,
        element: <Navigate to="history" replace />,
    },
    {
        path: "history",
        element: <MessageList />,
    },
    {
        path: "new",
        element: <MessageAdd />,
    },
    {
        path: ":id",
        element: <MessageShow />,
    },
];
