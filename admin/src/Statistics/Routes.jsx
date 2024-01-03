import React from "react";
import { Route, Switch } from "react-router-dom";
import StatisticsOverview from "./StatisticsOverview";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={StatisticsOverview} />
        <Route
            path={`${match.path}/statisticsz`}
            component={StatisticsOverview}
        />
    </Switch>
);
