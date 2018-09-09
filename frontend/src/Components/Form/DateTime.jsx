import React from 'react';


const DateTime = ({date}) => {
    let res = <em>Ej angivet</em>;
    
    if (date) {
        const options = {
            year:   'numeric', month: 'numeric', day: 'numeric',
            hour:   'numeric', minute: 'numeric', second: 'numeric',
            hour12: false
        };
        
        // Parse the date
        let parsed_date = Date.parse(date);
        
        // If the date was parsed successfully we should update the string
        if (!isNaN(parsed_date)) {
            res = new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
        }
    }
    
    return (<span>{res}</span>);
};


export default DateTime;