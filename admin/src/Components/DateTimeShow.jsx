import React from 'react';
import {dateTimeToStr} from "../utils";


const DateTimeShow = ({date}) => {
    if (date) {
        return <span>{dateTimeToStr(date)}</span>;
    }
    
    return <span><em>Not set</em></span>;
};


export default DateTimeShow;