import About from "./About";
import AccessTokenList from "./AccessTokenList";
import ServiceTokenList from "./ServiceTokenList";
import { Route, Switch } from "react-router-dom";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={About} />
        <Route path={`${match.path}/about`} component={About} />
        <Route path={`${match.path}/tokens`} component={AccessTokenList} />
        <Route
            path={`${match.path}/service_tokens`}
            component={ServiceTokenList}
        />
    </Switch>
);
