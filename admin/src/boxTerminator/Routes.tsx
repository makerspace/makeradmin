import React from "react";
import { Route, Switch, match } from "react-router-dom";
import BoxTerminator from "./BoxTerminator";

export default ({ match }: { match: match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={BoxTerminator} />
    </Switch>
);
