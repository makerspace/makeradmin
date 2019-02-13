module.exports = {
    childRoutes: [
        {
            path: "/statistics",
            indexRoute: {
                component: require("./StatisticsOverview").default
            },
        }
    ]
};
