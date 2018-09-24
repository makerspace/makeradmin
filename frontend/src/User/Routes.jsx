module.exports = {
    path: "member",
    indexRoute: {
        component: require("./Member").default,
    },
    childRoutes: [
        {
            path: "login/:token",
            component: require("./Login").default,
        }
    ]
};
