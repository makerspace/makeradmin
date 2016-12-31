module.exports = {
	childRoutes: [
		{
			path: "/keys",
			indexRoute: {
				component: require("./Pages/List")
			},
			childRoutes: [
				{
					path: "add",
					component: require("./Pages/Add")
				},
				{
					path: ":id",
					component: require("./Pages/Show")
				},
			]
		}
	]
}