import React from "react";
import { Navigate, Route, useLocation } from "react-router";

type RedirectProps = {
    subpage: string;
};

export function url_join([...paths]: string[]): string {
    const paths_without_trailing_slashes = paths.map((path) =>
        path.replace(/\/$/, ""),
    );
    return paths_without_trailing_slashes.join("/");
}

export const RedirectToSubpage = ({ subpage }: RedirectProps) => {
    const location = useLocation();
    const to = url_join([location.pathname, subpage]);
    return <Navigate to={to} replace={true} />;
};
