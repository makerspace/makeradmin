module.exports = {
    path: "member",
    indexRoute: {
        component: require("./Member"),
    },
    childRoutes: [
        {
            path: "login/:token",
            component: require("./Login"),
        }
    ]
};
