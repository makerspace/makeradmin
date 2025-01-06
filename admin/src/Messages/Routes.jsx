import React from "react";
import { Route, Switch } from "react-router-dom";
import { defaultSubpageRoute } from "../Components/Routes";
import MessageAdd from "./MessageAdd";
import MessageList from "./MessageList";
import MessageShow from "./MessageShow";

export default ({ match }) => (
    <Switch>
        {defaultSubpageRoute({ matchpath: match.path, subpage: "history" })}
        <Route path={`${match.path}/history`} component={MessageList} />
        <Route path={`${match.path}/new`} component={MessageAdd} />
        <Route path={`${match.path}/:id`} component={MessageShow} />
    </Switch>
);
