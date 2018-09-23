import React from 'react';
import {dateTimeToStr} from "../utils";


const DateTimeShow = ({date}) => {
    if (date) {
        return <span>{dateTimeToStr(date)}</span>;
    }
    
    return <span><em>Ej angivet</em></span>;
};


export default DateTimeShow;