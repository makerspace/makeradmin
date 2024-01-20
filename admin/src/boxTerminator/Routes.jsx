import BoxTerminator from "./BoxTerminator";
import { Route, Switch } from "react-router-dom";

export default ({ match }) => (
    <Switch>
        <Route path={`${match.path}/`} exact component={BoxTerminator} />
    </Switch>
);
