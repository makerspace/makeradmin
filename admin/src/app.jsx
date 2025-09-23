import "uikit/dist/css/uikit.css";

import UIkit from "uikit";
import Icons from "uikit/dist/js/uikit-icons";
UIkit.use(Icons);

import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Outlet } from "react-router";
import { Route, Routes } from "react-router-dom";
import Page404 from "./Components/404";
import Login from "./Components/Login";
import Logout from "./Components/Logout";
import PasswordReset from "./Components/PasswordReset";
import RequestPasswordReset from "./Components/RequestPasswordReset";
import auth from "./auth";
import { Nav, SideNav } from "./nav";

import { RedirectToSubpage } from "./Components/Routes";
import Membership from "./Membership/Routes";
import Messages from "./Messages/Routes";
import Quiz from "./Quiz/Routes";
import Sales from "./Sales/Routes";
import Settings from "./Settings/Routes";
import Statistics from "./Statistics/Routes";
import BoxTerminator from "./boxTerminator/Routes";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

const nav = {
    brand: "MakerAdmin",
    items: [
        {
            text: "Medlemmar",
            target: "/membership",
            icon: "user",
            children: [
                {
                    text: "Medlemmar",
                    target: "/membership/members",
                    icon: "user",
                },
                {
                    text: "Grupper",
                    target: "/membership/groups",
                    icon: "users",
                },
                {
                    text: "Nycklar",
                    target: "/membership/keys",
                    icon: "key",
                },
                {
                    text: "Medlemsperioder",
                    target: "/membership/spans",
                    icon: "clock",
                },
                {
                    text: "Exportera medlemmar",
                    target: "/membership/export",
                    icon: "download",
                },
            ],
        },
        {
            text: "Försäljning",
            target: "/sales",
            icon: "cart",
            children: [
                {
                    text: "Ordrar",
                    target: "/sales/order",
                },
                {
                    text: "Presentkort",
                    target: "/sales/gift-card",
                },
                {
                    text: "Produkter",
                    target: "/sales/product",
                },
                {
                    text: "Bilder",
                    target: "/sales/image",
                },
                {
                    text: "Kategorier",
                    target: "/sales/category",
                },
                {
                    text: "Bokföring",
                    target: "/sales/accounting",
                },
            ],
        },
        {
            text: "Utskick",
            target: "/messages",
            icon: "mail",
            children: [
                {
                    text: "Historik",
                    target: "/messages/history",
                    icon: "list",
                },
                {
                    text: "Nytt utskick",
                    target: "/messages/new",
                    icon: "reply",
                },
            ],
        },
        {
            text: "Quiz",
            target: "/quiz",
            icon: "commenting",
            children: [
                {
                    text: "Quiz",
                    target: "/quiz",
                },
            ],
        },
        {
            text: "Statistik",
            target: "/statistics",
            icon: "image",
            children: [
                {
                    text: "Sales by Product",
                    target: "/statistics/product/sales",
                },
                {
                    text: "Sales by Category",
                    target: "/statistics/category/sales",
                },
                {
                    text: "Quiz",
                    target: "/statistics/quiz",
                },
                {
                    text: "Membership",
                    target: "/statistics/membership",
                },
                {
                    text: "Physical Access Log",
                    target: "/statistics/physical_access_log",
                },
                {
                    text: "Members of Interest",
                    target: "/statistics/members_of_interest",
                },
            ],
        },
        {
            text: "Inställningar",
            target: "/settings",
            icon: "cog",
            children: [
                {
                    text: "About",
                    target: "/settings/about",
                },
                {
                    text: "My access tokens",
                    target: "/settings/tokens",
                },
                {
                    text: "Service tokens",
                    target: "/settings/service_tokens",
                },
            ],
        },
        {
            text: "boxTerminator",
            target: "/boxTerminator",
            icon: "camera",
        },
        {
            text: "Logga ut",
            target: "/logout",
            icon: "sign-out",
        },
    ],
};

const ContentWrapper = () => {
    const [isLoggedIn, setIsLoggedIn] = React.useState(auth.isLoggedIn());

    React.useEffect(() => {
        auth.onChange = (status) => setIsLoggedIn(status);
    }, []);

    console.log("AAAAA ", isLoggedIn);

    if (!isLoggedIn) {
        return <Login />;
    }

    return (
        <div style={{ marginBottom: "2em" }}>
            <Nav nav={nav} className="uk-margin-top" />
            <div className="uk-container uk-margin-top">
                <div className="uk-grid">
                    <div className="uk-width-1-4@m">
                        <SideNav nav={nav} />
                    </div>
                    <div className="uk-width-3-4@m">
                        <Outlet />
                    </div>
                </div>
            </div>
        </div>
    );
};

const router = createBrowserRouter([
    {
        path: "/logout",
        Component: Logout,
    },
    {
        path: "/request-password-reset",
        Component: RequestPasswordReset,
    },
    {
        path: "/password-reset",
        Component: PasswordReset,
    },
    {
        path: "/*",
        Component: ContentWrapper,
        children: [
            {
                index: true,
                Component: () => <RedirectToSubpage subpage={"membership"} />,
            },
            {
                path: "membership/*",
                children: Membership,
            },
            {
                path: "sales/*",
                children: Sales,
            },
            {
                path: "messages/*",
                children: Messages,
            },
            {
                path: "statistics/*",
                children: Statistics,
            },
            {
                path: "settings/*",
                children: Settings,
            },
            {
                path: "quiz/*",
                children: Quiz,
            },
            {
                path: "boxTerminator/*",
                children: BoxTerminator,
            },
            {
                path: "*",
                Component: Page404,
            },
        ],
    },
]);

const App = () => <RouterProvider router={router} />;

App.title = "MakerAdmin";

createRoot(document.getElementById("main")).render(<App />);
