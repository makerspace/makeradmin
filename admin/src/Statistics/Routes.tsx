import React from "react";
import { Route, Switch, match } from "react-router-dom";
import { defaultSubpageRoute } from "../Components/Routes";
import AccessLogPage from "./AccessLogPage";
import MembershipPage from "./MembershipPage";
import MembersOfInterestPage from "./MembersOfInterestPage";
import QuizPage from "./QuizPage";
import SalesByCategoryPage from "./SalesByCategoryPage";
import SalesByProductPage from "./SalesByProductPage";

export default ({ match }: { match: match }) => (
    <Switch>
        {defaultSubpageRoute({
            matchpath: match.path,
            subpage: "product/sales",
        })}
        <Route
            path={`${match.path}/product/sales`}
            component={SalesByProductPage}
        />
        <Route
            path={`${match.path}/category/sales`}
            component={SalesByCategoryPage}
        />
        <Route path={`${match.path}/quiz`} component={QuizPage} />
        <Route path={`${match.path}/membership`} component={MembershipPage} />
        <Route
            path={`${match.path}/physical_access_log`}
            component={AccessLogPage}
        />
        <Route
            path={`${match.path}/members_of_interest`}
            component={MembersOfInterestPage}
        />
    </Switch>
);
