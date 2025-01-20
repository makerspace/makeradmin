import React from "react";
import { MembershipGraph } from "./Graphs/MembershipGraph";
import {
    RetentionGraph,
    RetentionGraphExplanation,
} from "./Graphs/RetentionGraph";

export default () => {
    return (
        <div className="uk-width-1-1">
            <h2>Membership Statistics</h2>
            <MembershipGraph />
            <hr />
            <h2>Membership Retention</h2>
            <RetentionGraph />
            <RetentionGraphExplanation />
            <hr />
        </div>
    );
};
