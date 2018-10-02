// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')
require('uikit/dist/js/components/notify')
require('uikit/dist/js/components/upload')

// React stuff
import React from 'react';
import ReactDOM from 'react-dom';
import {Router,	browserHistory} from 'react-router';

const rootRoute = {
    childRoutes: [
        {
            path: "/",
            indexRoute: {
                component: require("./User/Member").default,
            },
            childRoutes: [
                {
                    path: "member",
                    onEnter: (nextState, replace) => replace("/"),
                },
                {
                    path: "login/:token",
                    component: require("./User/Login").default,
                },
                {
                    path: "*",
                    component: require("./Components/404").default,
                },
            ]
        },
    ]
};

ReactDOM.render(<Router history={browserHistory} routes={rootRoute}/>, document.getElementById("main"));
