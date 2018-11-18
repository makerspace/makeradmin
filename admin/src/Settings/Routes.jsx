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
                    path: "about",
                    component: require("./About").default,
                },
            ]
        },
    ]
};
