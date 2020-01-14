module.exports = {
    childRoutes: [
        {
            path: "settings",
            indexRoute: {
                onEnter: (nextState, replace) => replace("/settings/about"),
            },
            childRoutes: [
                {
                    path: "tokens",
                    component: require("./AccessTokenList").default,
                },
                {
                    path: "service_tokens",
                    component: require("./ServiceTokenList").default,
                },
                {
                    path: "about",
                    component: require("./About").default,
                },
            ]
        },
    ]
};
