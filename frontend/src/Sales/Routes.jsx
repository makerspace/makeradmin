module.exports = {
	childRoutes: [
		{
			path: "/sales",
			indexRoute: {
				component: require("./Pages/Product/List"),
			},
			childRoutes: [
				{
					path: "product",
					component: require("./Pages/Product/List"),
				},
				{
					path: "product/add",
					component: require("./Pages/Product/Add"),
				},
				{
					path: "product/:id",
					component: require("./Pages/Product/Edit"),
				},
				{
					path: "order",
					component: require("./Pages/Order/List"),
				},
				{
					path: "order/:id",
					component: require("./Pages/Order/View"),
				},
			]
		}
	]
};
