import React from "react";
import { Route, Switch } from "react-router-dom";
import BoxTerminator from "./BoxTerminator";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={BoxTerminator} />
    </Switch>
);
