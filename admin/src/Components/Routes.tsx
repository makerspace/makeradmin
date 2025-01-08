import React from "react";
import { match, Redirect, Route, useLocation } from "react-router";

type RedirectProps = {
    subpage: string;
};

export function url_join([...paths]: string[]): string {
    const paths_without_trailing_slashes = paths.map((path) =>
        path.replace(/\/$/, ""),
    );
    return paths_without_trailing_slashes.join("/");
}

const RedirectToSubpage = ({ subpage }: RedirectProps) => {
    const location = useLocation();
    const to = url_join([location.pathname, subpage]);
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
