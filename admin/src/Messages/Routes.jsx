import MessageAdd from "./MessageAdd";
import MessageList from "./MessageList";
import MessageShow from "./MessageShow";
import { Route, Switch } from "react-router-dom";

export default ({ match }) => (
    <Switch>
        <Route exact path={`${match.path}/`} component={MessageList} />
        <Route path={`${match.path}/history`} component={MessageList} />
        <Route path={`${match.path}/new`} component={MessageAdd} />
        <Route path={`${match.path}/:id`} component={MessageShow} />
    </Switch>
);
