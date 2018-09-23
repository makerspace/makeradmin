import React from 'react';
import * as _ from "underscore";
import {dateToStr} from "../utils";


const DateShow = props => {
    if (!_.isEmpty(props.date)) {
        return <span>{dateToStr(props.date)}</span>;
    }
    
    return <span><em>Ej angivet</em></span>;
};

export default DateShow;
