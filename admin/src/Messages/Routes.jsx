module.exports = {
    childRoutes: [
        {
            path: "messages",
            indexRoute: {
                onEnter: (nextState, replace) => replace("/messages/history"),
            },
            childRoutes: [
                {
                    path: "history",
                    component: require("./MessageList").default
                },
                {
                    path: "new",
                    component: require("./MessageAdd").default
                },
                {
                    path: ":id",
                    component: require("./MessageShow").default
                },
            ]
        },
    ]
};
