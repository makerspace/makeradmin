module.exports = {
	childRoutes: [
		{
			path: "/membership",
			indexRoute: {
				onEnter: (nextState, replace) => replace("/membership/members"),
			},
			childRoutes: [
                {
                    path: "membersx",
                    indexRoute: {
                        component: require("./MemberList").default,
                    },
					childRoutes: [
                        {
                            path: "add",
                            component: require("./MemberAdd").default,
                        },
                        {
                            path: ":member_id",
                            component:  require("./MemberBox").default,
                            indexRoute: {
                                component: require("./Member/MemberInfoTab").default,
							},
							childRoutes: [
								{
									path: "info",
									component: require("./Member/MemberInfoTab").default,
								},
							]
                        },
					],
                },
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
							component: require("./Pages/Member/Show").default,
							indexRoute: {
								component: require("./Components/UserBox/User/Show").default,
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
										component: require("./Components/UserBox/Keys/List"),
									},
									childRoutes: [
										{
											path: "add",
											component: require("./Components/UserBox/Keys/Add"),
										},
										{
											path: ":key_id",
											component: require("./Components/UserBox/Keys/Edit"),
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
				{
					path: "keys",
					indexRoute: {
						component: require("./Pages/Key/List")
					},
					childRoutes: [
						{
							path: "add",
							component: require("./Pages/Key/Add")
						},
						{
							path: ":id",
							component: require("./Pages/Key/Show")
						},
					]
				},
				{
					path: "spans",
					indexRoute: {
						component: require("./Pages/Span/List"),
					},
					childRoutes: [
						{
							path: ":span_id",
							component: require("./Pages/Span/Show"),
						},
					],
				},
			]
		},
	]
}