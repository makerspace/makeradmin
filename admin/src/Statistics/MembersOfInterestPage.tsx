import React from "react";
import MostActiveMembers from "./MostActiveMembers";

export default () => {
    return (
        <div className="uk-width-1-1">
            <h2>Members of interest</h2>
            <p>
                Members have been scored in different categories based on, for
                example: how much they have bought of specific products or how
                many days they open a specific door.
            </p>
            <MostActiveMembers />
        </div>
    );
};
