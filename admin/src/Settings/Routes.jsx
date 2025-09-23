import React from "react";
import { RedirectToSubpage } from "../Components/Routes";
import About from "./About";
import AccessTokenList from "./AccessTokenList";
import ServiceTokenList from "./ServiceTokenList";

const routes = [
    {
        index: true,
        element: <RedirectToSubpage subpage={"about"} />,
    },
    {
        path: "about",
        element: <About />,
    },
    {
        path: "tokens",
        element: <AccessTokenList />,
    },
    {
        path: "service_tokens",
        element: <ServiceTokenList />,
    },
];

export default routes;
