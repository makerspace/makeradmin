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
                    component: require("./MessageNew").default
                },
				{
					path: "templates",
					component: require("./Pages/Templates/List"),
				},
				{
					path: "templates/new",
					component: require("./Pages/Templates/Add"),
				},
				{
					path: "templates/:id",
					component: require("./Pages/Templates/Edit"),
				},
				{
					path: ":id",
					component: require("./Pages/Messages/Show")
				},
			]
		},
	]
}