module.exports = {
	childRoutes: [
		{
			path: "/auto",
			indexRoute: {
				onEnter: (nextState, replace) => replace("/auto/overview"),
			},
			childRoutes: [
				{
					path: "overview",
					component: require("./Pages/Test"),
				},
				{
					path: "tictail",
					component: require("../Tictail/Pages/Overview"),
				},
				{
					path: "verification",
					component: require("./Pages/Verification"),
				},
				{
					path: "multiaccess",
					component: require("./Pages/Multiaccess"),
				},
			]
		},
	]
}