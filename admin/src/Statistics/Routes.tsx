import React from "react";
import { Route, Routes } from "react-router-dom";
import { RedirectToSubpage } from "../Components/Routes";
import AccessLogPage from "./AccessLogPage";
import MembershipPage from "./MembershipPage";
import MembersOfInterestPage from "./MembersOfInterestPage";
import QuizPage from "./QuizPage";
import SalesByCategoryPage from "./SalesByCategoryPage";
import SalesByProductPage from "./SalesByProductPage";
import { RouteObject } from "react-router-dom";

const routes: RouteObject[] = [
    {
        index: true,
        element: <RedirectToSubpage subpage={"product/sales"} />,
    },
    {
        path: "product/sales",
        element: <SalesByProductPage />,
    },
    {
        path: "category/sales",
        element: <SalesByCategoryPage />,
    },
    {
        path: "quiz",
        element: <QuizPage />,
    },
    {
        path: "membership",
        element: <MembershipPage />,
    },
    {
        path: "physical_access_log",
        element: <AccessLogPage />,
    },
    {
        path: "members_of_interest",
        element: <MembersOfInterestPage />,
    },
];

export default routes;
