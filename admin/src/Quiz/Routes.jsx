import QuestionAdd from "./QuestionAdd";
import QuestionShow from "./QuestionShow";
import QuizAdd from "./QuizAdd";
import QuizList from "./QuizList";
import QuizShow from "./QuizShow";
import { Route, Switch } from "react-router-dom";

export default ({ match }) => {
    return (
        <Switch>
            <Route path={match.path} exact component={QuizList} />
            <Route path={`${match.path}/add`} exact component={QuizAdd} />
            <Route path={`${match.path}/:id`} exact component={QuizShow} />
            <Route
                path={`${match.path}/:quiz_id/question/add`}
                component={QuestionAdd}
            />
            <Route
                path={`${match.path}/question/:id`}
                component={QuestionShow}
            />
        </Switch>
    );
};
