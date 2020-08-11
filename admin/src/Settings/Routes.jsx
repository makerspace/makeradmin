import React from 'react';
import { Route, Switch } from 'react-router-dom';
import AccessTokenList from "./AccessTokenList";
import ServiceTokenList from "./ServiceTokenList";
import About from "./About";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={About} />
        <Route path={`${match.path}/about`} component={About} />
        <Route path={`${match.path}/tokens`} component={AccessTokenList} />
        <Route path={`${match.path}/service_tokens`} component={ServiceTokenList} />
    </Switch>
)
