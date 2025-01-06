// Load jQuery and UIkit
global.jQuery = require("jquery");
global.$ = global.jQuery;
import "uikit/dist/css/uikit.css";

import UIkit from "uikit";
import Icons from "uikit/dist/js/uikit-icons";
UIkit.use(Icons);

import React from "react";
import ReactDOM from "react-dom";
import { Router } from "react-router";
import { Route, Switch } from "react-router-dom";
import Login from "./Components/Login";
import auth from "./auth";
import { browserHistory } from "./browser_history";
import { Nav, SideNav } from "./nav";

import Page404 from "./Components/404";
import Logout from "./Components/Logout";
import PasswordReset from "./Components/PasswordReset";
import RequestPasswordReset from "./Components/RequestPasswordReset";

import { defaultSubpageRoute } from "./Components/Routes";
import Membership from "./Membership/Routes";
import Messages from "./Messages/Routes";
import Quiz from "./Quiz/Routes";
import Sales from "./Sales/Routes";
import Settings from "./Settings/Routes";
import BoxTerminator from "./boxTerminator/Routes";

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
const App = () => {
    const [isLoggedIn, setIsLoggedIn] = React.useState(auth.isLoggedIn());

    React.useEffect(() => {
        auth.onChange = (status) => setIsLoggedIn(status);
    }, []);

    return (
        <Router history={browserHistory}>
            <Switch>
                <Route path="/logout" component={Logout} />
                <Route
                    path="/request-password-reset"
                    component={RequestPasswordReset}
                />
                <Route path="/password-reset" component={PasswordReset} />
                <Route path="*">
                    {isLoggedIn && (
                        <div style={{ marginBottom: "2em" }}>
                            <Nav nav={nav} />
                            <div className="uk-container uk-container uk-margin-top">
                                <div className="uk-grid">
                                    <div className="uk-width-1-4@m">
                                        <SideNav nav={nav} />
                                    </div>
                                    <div className="uk-width-3-4@m">
                                        <Switch>
                                            {defaultSubpageRoute({
                                                matchpath: "",
                                                subpage: "membership",
                                            })}
                                            <Route
                                                path="/membership"
                                                component={Membership}
                                            />
                                            <Route
                                                path="/sales"
                                                component={Sales}
                                            />
                                            <Route
                                                path="/messages"
                                                component={Messages}
                                            />
                                            <Route
                                                path="/settings"
                                                component={Settings}
                                            />
                                            <Route
                                                path="/quiz"
                                                component={Quiz}
                                            />
                                            <Route
                                                path="/boxTerminator"
                                                component={BoxTerminator}
                                            />
                                            <Route component={Page404} />
                                        </Switch>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    {!isLoggedIn && <Login />}
                </Route>
            </Switch>
        </Router>
    );
};

App.title = "MakerAdmin";

ReactDOM.render(<App />, document.getElementById("main"));
