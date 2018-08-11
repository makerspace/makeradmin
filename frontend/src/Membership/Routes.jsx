module.exports = {
	childRoutes: [
		{
			path: "/membership",
			indexRoute: {
				onEnter: (nextState, replace) => replace("/membership/members"),
			},
			childRoutes: [
				{
					path: "members",
					indexRoute: {
						component: require("./Pages/Member/List"),
					},
					childRoutes: [
						{
							path: "add",
							component: require("./Pages/Member/Add"),
						},
						{
							path: ":member_id",
							component: require("./Pages/Member/Show"),
							indexRoute: {
								component: require("./Components/UserBox/User/Show"),
							},
							childRoutes: [
								{
									path: "info",
									component: require("./Components/UserBox/User/Show"),
								},
								{
									path: "groups",
									indexRoute: {
										component: require("./Components/UserBox/Groups/List"),
									},
									childRoutes: [
										{
											path: "add",
											component: require("./Components/UserBox/Groups/Add"),
										},
									],
								},
								{
									path: "keys",
									indexRoute: {
										component: require("../Keys/Components/UserBox/List"),
									},
									childRoutes: [
										{
											path: "add",
											component: require("../Keys/Components/UserBox/Add"),
										},
										{
											path: ":key_id",
											component: require("../Keys/Components/UserBox/Edit"),
										},
									],
								},
								{
									path: "permissions",
									component: require("./Components/UserBox/Permissions/List"),
								},
								{
									path: "transactions",
									component: require("../Economy/Components/UserBox/List"),
								},
								{
									path: "messages",
									indexRoute: {
										component: require("../Messages/Components/UserBox/List"),
									},
									childRoutes: [
										{
											path: "new",
											component: require("../Messages/Components/UserBox/New"),
										},
									],
								},
							],
						},
					],
				},
				{
					path: "groups",
					indexRoute: {
						component: require("./Pages/Group/List"),
					},
					childRoutes: [
						{
							path: "add",
							component: require("./Pages/Group/Add"),
						},
						{
							path: ":group_id",
							component: require("./Pages/Group/Show"),
							indexRoute: {
								component: require("./Components/GroupBox/Groups/Show"),
							},
							childRoutes: [
								{
									path: "info",
									component: require("./Components/GroupBox/Groups/Show"),
								},
								{
									path: "members",
									indexRoute: {
										component: require("./Components/GroupBox/Member/List"),
									},
									childRoutes: [
										{
											path: "add",
											component: require("./Components/GroupBox/Member/Add"),
										},
									],
								},
								{
									path: "permissions",
									indexRoute: {
										component: require("./Components/GroupBox/Permissions/List"),
									},
									childRoutes: [
										{
											path: "add",
											component: require("./Components/GroupBox/Permissions/Add"),
										},
									],
								},
							],
						},
					],
				},
			]
		},
	]
}