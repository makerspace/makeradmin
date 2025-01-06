import React from "react";
import { match, Redirect, Route, useLocation } from "react-router";

type RedirectProps = {
    subpage: string;
};

const RedirectToSubpage = ({ subpage }: RedirectProps) => {
    const location = useLocation();
    const to = location.pathname.concat("/" + subpage);
    return <Redirect to={to} />;
};

type DefaultSubpageRouteParams = {
    matchpath: match["path"];
    subpage: string;
};

// Apparently we can't make it into a component itself, then it skips rendering
// the other routes, and never redirects
export const defaultSubpageRoute = ({
    matchpath,
    subpage,
}: DefaultSubpageRouteParams) => {
    return (
        <Route
            exact
            path={`${matchpath}/`}
            component={() => <RedirectToSubpage subpage={subpage} />}
        />
    );
};
