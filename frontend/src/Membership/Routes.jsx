module.exports = {
	childRoutes: [
		{
			path: "/members",
			indexRoute: {
				component: require("./Pages/Member/List")
			},
			childRoutes: [
				{
					path: "add",
					component: require("./Pages/Member/Add")
				},
				{
					path: ":id",
					component: require("./Pages/Member/Show")
				},
			]
		},
		{
			path: "/groups",
			indexRoute: {
				component: require("./Pages/Group/List")
			},
			childRoutes: [
				{
					path: "add",
					component: require("./Pages/Group/Add")
				},
				{
					path: ":id",
					component: require("./Pages/Group/Show")
				},
				{
					path: ":id/edit",
					component: require("./Pages/Group/Edit")
				},
			],
		}
	]
}