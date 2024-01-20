import StatisticsOverview from "./StatisticsOverview";
import { Route, Switch } from "react-router-dom";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={StatisticsOverview} />
        <Route
            path={`${match.path}/statisticsz`}
            component={StatisticsOverview}
        />
    </Switch>
);
