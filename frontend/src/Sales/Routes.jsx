module.exports = {
    childRoutes: [
        {
            path: "/sales",
            indexRoute: {
                onEnter: (nextState, replace) => replace("/sales/order"),
            },
            childRoutes: [
                {
                    path: "order",
                    component: require("./OrderList").default,
                },
                {
                    path: "order/:id",
                    component: require("./OrderShow").default,
                },
                {
                    path: "product",
                    component: require("./ProductList").default,
                },
				{
					path: "product/add",
					component: require("./Pages/Product/Add"),
				},
				{
					path: "product/:id",
					component: require("./Pages/Product/Edit"),
				},
			]
		}
	]
};
