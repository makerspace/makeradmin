module.exports = {
	childRoutes: [
		{
			path: "/sales",
			indexRoute: {
				component: require("./Pages/Overview")
			},
			childRoutes: [
				{
					path: "overview",
					component: require("./Pages/Overview")
				},
				{
					path: "products",
					component: require("./Pages/Products")
				},
				{
					path: "subscriptions",
					component: require("./Pages/Subscriptions")
				},
				{
					path: "history",
					component: require("./Pages/History")
				},
			]
		}
	]
}