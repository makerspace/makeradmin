import React from "react";
import { RedirectToSubpage } from "../Components/Routes";
import GroupAdd from "./GroupAdd";
import GroupBox from "./GroupBox";
import GroupBoxDoorAccess from "./GroupBoxDoorAccess";
import GroupBoxEditInfo from "./GroupBoxEditInfo";
import GroupBoxMembers from "./GroupBoxMembers";
import GroupBoxPermissions from "./GroupBoxPermissions";
import GroupList from "./GroupList";
import KeyEdit from "./KeyEdit";
import KeyHandout from "./KeyHandout";
import KeyList from "./KeyList";
import MemberAdd from "./MemberAdd";
import MemberBox from "./MemberBox";
import MemberBoxGroups from "./MemberBoxGroups";
import MemberBoxKeys from "./MemberBoxKeys";
import MemberBoxMemberData from "./MemberBoxMemberData";
import MemberBoxMessages from "./MemberBoxMessages";
import MemberBoxNewMessage from "./MemberBoxNewMessage";
import MemberBoxOrders from "./MemberBoxOrders";
import MemberBoxPermissions from "./MemberBoxPermissions";
import MemberBoxSpans from "./MemberBoxSpans";
import MemberBoxStatistics from "./MemberBoxStatistics";
import MemberExport from "./MemberExport";
import MemberList from "./MemberList";
import SpanList from "./SpanList";
import SpanShow from "./SpanShow";

const Group = {
    path: ":group_id/*",
    element: <GroupBox />,
    children: [
        {
            index: true,
            element: <RedirectToSubpage subpage={"info"} />,
        },
        {
            path: "info",
            element: <GroupBoxEditInfo />,
        },
        {
            path: "members",
            element: <GroupBoxMembers />,
        },
        {
            path: "permissions",
            element: <GroupBoxPermissions />,
        },
        {
            path: "doors",
            element: <GroupBoxDoorAccess />,
        },
    ],
};

const Groups = {
    path: "groups/*",
    children: [
        {
            index: true,
            element: <GroupList />,
        },
        {
            path: "add",
            element: <GroupAdd />,
        },
        Group,
    ],
};

const Member = {
    path: ":member_id/*",
    element: <MemberBox />,
    children: [
        {
            index: true,
            element: <RedirectToSubpage subpage={"key-handout"} />,
        },
        {
            path: "key-handout",
            element: <KeyHandout />,
        },
        {
            path: "member-data",
            element: <MemberBoxMemberData />,
        },
        {
            path: "groups",
            element: <MemberBoxGroups />,
        },
        {
            path: "keys",
            element: <MemberBoxKeys />,
        },
        {
            path: "permissions",
            element: <MemberBoxPermissions />,
        },
        {
            path: "orders",
            element: <MemberBoxOrders />,
        },
        {
            path: "messages/new",
            element: <MemberBoxNewMessage />,
        },
        {
            path: "messages",
            element: <MemberBoxMessages />,
        },
        {
            path: "spans",
            element: <MemberBoxSpans />,
        },
        {
            path: "statistics",
            element: <MemberBoxStatistics />,
        },
    ],
};

const Members = {
    path: "members/*",
    children: [
        {
            index: true,
            element: <MemberList />,
        },
        {
            path: "add",
            element: <MemberAdd />,
        },
        Member,
    ],
};

const Keys = {
    path: "keys/*",
    children: [
        {
            index: true,
            element: <KeyList />,
        },
        {
            path: ":key_id/*",
            element: <KeyEdit />,
        },
    ],
};

const Spans = {
    path: "spans/*",
    children: [
        {
            index: true,
            element: <SpanList />,
        },
        {
            path: ":span_id/*",
            element: <SpanShow />,
        },
    ],
};

const routes = [
    {
        path: "",
        element: <RedirectToSubpage subpage={"members"} />,
    },
    Members,
    Groups,
    Keys,
    Spans,
    {
        path: "export",
        element: <MemberExport />,
    },
];

export default routes;
