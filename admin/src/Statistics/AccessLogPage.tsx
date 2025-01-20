import React from "react";
import { AccessByHourGraph } from "./Graphs/AccessByHourGraph";
import { PhysicalAccessLogGraph } from "./Graphs/PhysicalAccessLogGraph";

export default () => {
    return (
        <div className="uk-width-1-1">
            <h2>Activity at the space</h2>
            <h3>Activity at the space by date</h3>
            <p>
                A visit is counted if a member opens at least one door during a
                day.
            </p>
            <PhysicalAccessLogGraph />
            <h3>Activity at the space by day of week</h3>
            <AccessByHourGraph />
        </div>
    );
};
