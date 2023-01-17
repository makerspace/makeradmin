import React from 'react';
import { Route, Switch } from 'react-router-dom';
// import AccessTokenList from "./AccessTokenList";
// import ServiceTokenList from "./ServiceTokenList";
import BoxTerminator from "./BoxTerminator";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={BoxTerminator} />
    </Switch>
);
