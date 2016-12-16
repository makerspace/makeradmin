module.exports = {
	childRoutes: [
		{
			path: "messages",
			indexRoute: {
				component: require("./Pages/List")
			},
			childRoutes: [
				{
					path: "new",
					component: require("./Pages/New")
				},
				{
					path: ":id/recipients",
					component: require("./Pages/Recipients")
				},
			]
		},
		{
			path: "settings",
			childRoutes: [
				{
					path: "mail/templates",
					component: require("./Pages/Templates"),
				},
			],
		},
	]
}