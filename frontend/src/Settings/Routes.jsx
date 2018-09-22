module.exports = {
    childRoutes: [
        {
            path: "settings",
            indexRoute: {
                component: require("./About").default,
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
