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
                                onEnter: (nextState, replace) => {
                                    return replace("/membership/members/" + nextState.params.member_id + "/member-data/");
                                },
                            },
                            childRoutes: [
                                {
                                    path: "member-data",
                                    component: require("./MemberBoxMemberData").default,
                                },
                                {
                                    path: "groups",
                                    component: require("./MemberBoxGroups").default,
                                },
                                {
                                    path: "keys",
                                    component: require("./MemberBoxKeys").default,
                                },
                                {
                                    path: "permissions",
                                    component: require("./MemberBoxPermissions").default,
                                },
                                {
                                    path: "orders",
                                    component: require("./MemberBoxOrders").default,
                                },
                                {
                                    path: "messages",
                                    indexRoute: {
                                        component: require("./MemberBoxMessages").default,
                                    },
                                    childRoutes: [
                                        {
                                            path: "new",
                                            component: require("./MemberBoxNewMessage").default,
                                        },
                                    ],
                                },
                                {
                                    path: "spans",
                                    component: require("./MemberBoxSpans").default,
                                },
                            ]
                        },
                    ],
                },
                {
                    path: "groups",
                    indexRoute: {
                        component: require("./GroupList").default,
                    },
                    childRoutes: [
                        {
                            path: "add",
                            component: require("./GroupAdd").default,
                        },
                        {
                            path: ":group_id",
                            component: require("./GroupBox").default,
                            indexRoute: {
                                component: require("./GroupBoxEditInfo").default,
                            },
                            childRoutes: [
                                {
                                    path: "info",
                                    component: require("./GroupBoxEditInfo").default,
                                },
                                {
                                    path: "members",
                                    component: require("./GroupBoxMembers").default,
                                },
                                {
                                    path: "permissions",
                                    component: require("./GroupBoxPermissions").default,
                                },
                            ],
                        },
                    ],
                },
                {
                    path: "keys",
                    indexRoute: {
                        component: require("./KeyList").default
                    },
                    childRoutes: [
                        {
                            path: ":key_id",
                            component: require("./KeyEdit").default
                        },
                    ]
                },
                {
                    path: "spans",
                    indexRoute: {
                        component: require("./SpanList").default,
                    },
                    childRoutes: [
                        {
                            path: ":span_id",
                            component: require("./SpanShow").default,
                        },
                    ],
                },
            ]
        },
    ]
};