// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')
require('uikit/dist/js/components/notify')
require('uikit/dist/js/components/upload')

import React from 'react';
import ReactDOM from 'react-dom';
import {Router,	browserHistory} from 'react-router';
import {Nav, SideNav} from './nav';
import auth from './auth';
import Login from './Components/Login';


const nav = {
    brand: "MakerAdmin 1.0",
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
                {
                    text: "Mallar",
                    target: "/messages/templates",
                    icon: "file-text-o",
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
                        text: "Access tokens",
                        target: "/settings/tokens",
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
        auth.onChange = isLoggedIn => this.setState({isLoggedIn});
    }

    render() {
        if (this.state.isLoggedIn) {
            return (
                <div>
                    <Nav nav={nav} />
                    <div className="uk-container uk-container-center uk-margin-top">
                        <div className="uk-grid">
                            <div className="uk-width-medium-1-4">
                                <SideNav nav={nav} />
                            </div>

                            <div className="uk-width-medium-3-4">
                                {this.props.children}
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return <Login/>;
    }
}
App.title = "MakerAdmin";

const rootRoute = {
    childRoutes: [
        require("./User/Routes"),
        {
            path: "resetpassword",
            component: require("./Components/ResetPassword").default,
        },
        {
            path: "/",
            component: App,
            indexRoute: {
                component: require("./Components/Dashboard").default,
            },
            childRoutes: [
                {
                    path: "logout",
                    component: require("./Components/Logout").default,
                },
                require("./Membership/Routes"),
                require("./Sales/Routes"),
                require("./Messages/Routes"),
                require("./Statistics/Routes"),
                require("./Settings/Routes"),
                {
                    path: "*",
                    component: require("./Components/404").default,
                },
            ]
        }
    ]
};


ReactDOM.render(<Router history={browserHistory} routes={rootRoute} />, document.getElementById("main"));
