
// Load jQuery and UIkit
global.jQuery = require('jquery');
global.$ = global.jQuery;
require('uikit');
require('uikit/dist/js/core/dropdown');
require('uikit/dist/js/components/pagination');
require('uikit/dist/js/components/autocomplete');
require('uikit/dist/js/components/notify');
require('uikit/dist/js/components/upload');

import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router';
import { Route, Switch } from 'react-router-dom';
import { browserHistory } from './browser_history';
import { Nav, SideNav } from './nav';
import auth from './auth';
import Login from './Components/Login';

import RequestPasswordReset from "./Components/RequestPasswordReset";
import PasswordReset from "./Components/PasswordReset";
import Logout from "./Components/Logout";
import Page404 from "./Components/404";
import Dashboard from './Components/Dashboard';

import Sales from "./Sales/Routes";
import Membership from "./Membership/Routes";
import Messages from "./Messages/Routes";
import Statistics from "./Statistics/Routes";
import Settings from "./Settings/Routes";
import Quiz from "./Quiz/Routes";

const nav = {
    brand: "MakerAdmin",
    items: [
        {
            text: "Medlemmar",
            target: "/membership",
            icon: "user",
            children:
                [
                    {
                        text: "Medlemmar",
                        target: "/membership/members",
                        icon: "user",
                    },
                    {
                        text: "Grupper",
                        target: "/membership/groups",
                        icon: "group",
                    },
                    {
                        text: "Nycklar",
                        target: "/membership/keys",
                        icon: "key",
                    },
                    {
                        text: "Medlemsperioder",
                        target: "/membership/spans",
                        icon: "clock-o",
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
            icon: "shopping-basket",
            children:
                [
                    {
                        text: "Ordrar",
                        target: "/sales/order",
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
                        text: "Bokförings konton",
                        target: "/sales/transaction_accounts",
                    },
                ],
        },
        {
            text: "Utskick",
            target: "/messages",
            icon: "envelope",
            children: [
                {
                    text: "Historik",
                    target: "/messages/history",
                    icon: "list",
                },
                {
                    text: "Nytt utskick",
                    target: "/messages/new",
                    icon: "envelope",
                },
            ],
        },
        {
            text: "Quiz",
            target: "/quiz",
            icon: "commenting",
            children:
                [
                    {
                        text: "Quiz",
                        target: "/quiz",
                    },
                ],
        },
        {
            text: "Statistik",
            target: "/statistics",
            icon: "area-chart",
        },
        {
            text: "Inställningar",
            target: "/settings",
            icon: "cog",
            children:
                [
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
            text: "Logga ut",
            target: "/logout",
            icon: "sign-out",
        },
    ]
};


class App extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            isLoggedIn: auth.isLoggedIn()
        };
    }

    componentDidMount() {
        auth.onChange = isLoggedIn => this.setState({ isLoggedIn });
    }

    render() {
        return (
            <Router history={browserHistory}>
                <Switch>
                    <Route path="/logout" component={Logout} />
                    <Route path="/request-password-reset" component={RequestPasswordReset} />
                    <Route path="/password-reset" component={PasswordReset} />
                    <Route path="*">
                        {this.state.isLoggedIn && (
                            <div style={{ marginBottom: "2em" }}>
                                <Nav nav={nav} />
                                <div className="uk-container uk-container-center uk-margin-top">
                                    <div className="uk-grid">
                                        <div className="uk-width-medium-1-4">
                                            <SideNav nav={nav} />
                                        </div>
                                        <div className="uk-width-medium-3-4">
                                            <Switch>
                                                <Route exact path="/" component={Dashboard} />
                                                <Route path="/membership" component={Membership} />
                                                <Route path="/sales" component={Sales} />
                                                <Route path="/messages" component={Messages} />
                                                <Route path="/statistics" component={Statistics} />
                                                <Route path="/settings" component={Settings} />
                                                <Route path="/quiz" component={Quiz} />
                                                <Route component={Page404} />
                                            </Switch>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                        {!this.state.isLoggedIn && <Login />}
                    </Route>
                </Switch>
            </Router>
        );
    }
}
App.title = "MakerAdmin";

ReactDOM.render(<App />, document.getElementById("main"));
