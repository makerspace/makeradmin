module.exports = {
	path: "settings",
	childRoutes: [
		{
			path: "export",
			component: require("./Pages/Export")
		},
		{
			path: "import",
			component: require("./Pages/Import")
		},
	]
}