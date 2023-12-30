import React from "react";
import { dateToStr } from "../utils";

const DateShow = ({ date }) => {
    if (date) {
        return <span>{dateToStr(date)}</span>;
    }

    return (
        <span>
            <em>Not set</em>
        </span>
    );
};

export default DateShow;
