import React from 'react';
import * as _ from "underscore";

// Fix all data show components.
const DateComponent = props => {
    
    if (!_.isEmpty(props.date)) {
        const options = {
            year: 'numeric', month: 'numeric', day: 'numeric', hour12: false
        };
        
        const parsed_date = Date.parse(props.date);
        
        // If the date was parsed successfully we should update the string
        if (!isNaN(parsed_date)) {
            return <span>{new Intl.DateTimeFormat("sv-SE", options).format(parsed_date)}</span>;
        }
    }
    
    return <span><em>Ej angivet</em></span>;
};

export default DateComponent;