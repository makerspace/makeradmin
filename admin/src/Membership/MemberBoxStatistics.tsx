import React from "react";
import { useParams } from "react-router-dom";
import { AccessByHourGraph } from "Statistics/Graphs/AccessByHourGraph";
import { PhysicalAccessLogGraph } from "Statistics/Graphs/PhysicalAccessLogGraph";

export default () => {
    const { member_id: member_id_str } = useParams<{ member_id?: string }>();
    const member_id = member_id_str ? parseInt(member_id_str) : undefined;

    if (member_id === undefined) return null;

    return (
        <div className="uk-width-1-1">
            <h2>Activity at the space</h2>
            <h3>Activity at the space by date</h3>
            <PhysicalAccessLogGraph member_id={member_id} />
            <h3>Activity at the space by day of week</h3>
            <AccessByHourGraph member_id={member_id} />
        </div>
    );
};
