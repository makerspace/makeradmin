import React from 'react';
import QuestionList from "./QuestionList";
import QuestionAdd from "./QuestionAdd";
import QuestionShow from "./QuestionShow";
import { Route, Switch } from 'react-router-dom';

export default ({ match }) => {
    return (
        <Switch>
            <Route path={match.path} exact component={QuestionList} />
            <Route path={`${match.path}/question`} exact component={QuestionList} />
            <Route path={`${match.path}/question/add`} component={QuestionAdd} />
            <Route path={`${match.path}/question/:id`} component={QuestionShow} />
        </Switch>
    );
};
