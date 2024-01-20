import GroupAdd from "./GroupAdd";
import GroupBox from "./GroupBox";
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
import MemberExport from "./MemberExport";
import MemberList from "./MemberList";
import SpanList from "./SpanList";
import SpanShow from "./SpanShow";
import { Route, Switch } from "react-router-dom";

const Group = ({ match: { path } }) => (
    <GroupBox>
        <Switch>
            <Route exact path={`${path}/`} component={GroupBoxEditInfo} />
            <Route path={`${path}/info`} component={GroupBoxEditInfo} />
            <Route path={`${path}/members`} component={GroupBoxMembers} />
            <Route
                path={`${path}/permissions`}
                component={GroupBoxPermissions}
            />
        </Switch>
    </GroupBox>
);

const Groups = ({ match: { path } }) => (
    <Switch>
        <Route exact path={path} component={GroupList} />
        <Route path={`${path}/add`} component={GroupAdd} />
        <Route path={`${path}/:group_id`} component={Group} />
    </Switch>
);

const Member = ({ match: { path } }) => (
    <MemberBox>
        <Switch>
            <Route exact path={`${path}/`} component={KeyHandout} />
            <Route path={`${path}/key-handout`} component={KeyHandout} />
            <Route
                path={`${path}/member-data`}
                component={MemberBoxMemberData}
            />
            <Route path={`${path}/groups`} component={MemberBoxGroups} />
            <Route path={`${path}/keys`} component={MemberBoxKeys} />
            <Route
                path={`${path}/permissions`}
                component={MemberBoxPermissions}
            />
            <Route path={`${path}/orders`} component={MemberBoxOrders} />
            <Route
                path={`${path}/messages/new`}
                component={MemberBoxNewMessage}
            />
            <Route path={`${path}/messages`} component={MemberBoxMessages} />
            <Route path={`${path}/spans`} component={MemberBoxSpans} />
        </Switch>
    </MemberBox>
);

const Members = ({ match: { path } }) => (
    <Switch>
        <Route exact path={path} component={MemberList} />
        <Route path={`${path}/add`} component={MemberAdd} />
        <Route path={`${path}/:member_id`} component={Member} />
    </Switch>
);

const Keys = ({ match: { path } }) => (
    <Switch>
        <Route exact path={path} component={KeyList} />
        <Route path={`${path}/:key_id`} component={KeyEdit} />
    </Switch>
);

const Spans = ({ match: { path } }) => (
    <Switch>
        <Route exact path={path} component={SpanList} />
        <Route path={`${path}/:span_id`} component={SpanShow} />
    </Switch>
);

export default ({ match }) => (
    <Switch>
        <Route exact path={match.path} component={MemberList} />
        <Route path={`${match.path}/members`} component={Members} />
        <Route path={`${match.path}/groups`} component={Groups} />
        <Route path={`${match.path}/keys`} component={Keys} />
        <Route path={`${match.path}/spans`} component={Spans} />
        <Route path={`${match.path}/export`} component={MemberExport} />
    </Switch>
);
