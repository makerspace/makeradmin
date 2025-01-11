import React from "react";

export const CenteredForm = ({ children }) => {
    return (
        <div className="uk-flex uk-flex-center uk-flex-middle uk-text-center uk-height-1-1">
            <div
                className="uk-vertical-align-middle"
                style={{ width: "500px" }}
            >
                <div className="uk-text-left">{children}</div>
            </div>
        </div>
    );
};
