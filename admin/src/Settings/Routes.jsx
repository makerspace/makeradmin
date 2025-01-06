import React from "react";
import { Route, Switch } from "react-router-dom";
import { defaultSubpageRoute } from "../Components/Routes";
import About from "./About";
import AccessTokenList from "./AccessTokenList";
import ServiceTokenList from "./ServiceTokenList";

export default ({ match }) => (
    <Switch>
        {defaultSubpageRoute({ matchpath: match.path, subpage: "about" })}
        <Route path={`${match.path}/about`} component={About} />
        <Route path={`${match.path}/tokens`} component={AccessTokenList} />
        <Route
            path={`${match.path}/service_tokens`}
            component={ServiceTokenList}
        />
    </Switch>
);
