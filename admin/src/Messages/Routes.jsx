import React from 'react';
import { Route, Switch } from 'react-router-dom';
import MessageList from "./MessageList"
import MessageAdd from "./MessageAdd"
import MessageShow from "./MessageShow"

export default ({ match }) => (
    <Switch>
        <Route exact path={`${match.path}/`} component={MessageList} />
        <Route path={`${match.path}/history`} component={MessageList} />
        <Route path={`${match.path}/new`} component={MessageAdd} />
        <Route path={`${match.path}/:id`} component={MessageShow} />
    </Switch>
)
