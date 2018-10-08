import * as _ from "underscore";

window._ = _;

// eslint-disable-next-line
export const assert = expression => console.assert(expression);


const utcDateFormat = Intl.DateTimeFormat("sv-SE", {timeZone: "UTC", year: 'numeric', month: '2-digit', day: '2-digit'});


export const formatUtcDate = date => utcDateFormat.format(date);


export const parseUtcDate = str => {
    if (/\d{4}-\d{2}-\d{2}/.test(str)) {
        const d = new Date(str + "T00:00:00.000Z");
        if (isNaN(d)) {
            return null;
        }
        return d;
    }
    return null;
};


export const utcToday = () => {const d = new Date(); d.setUTCHours(0, 0, 0, 0); return d;};


export const addToDate = (date, millis) => new Date(date.getTime() + millis);


export const dateToStr = date => {
    if (!_.isEmpty(date)) {
        const options = {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour12: false
        };
        
        const parsed_date = Date.parse(date);
        
        // If the date was parsed successfully we should update the string
        if (!isNaN(parsed_date)) {
            return new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
        }
    }
    return "";
};


export const dateTimeToStr = date => {
    if (!_.isEmpty(date)) {
        const options = {
            year: 'numeric', month: 'numeric', day: 'numeric',
            hour: 'numeric', minute: 'numeric', second: 'numeric',
            hour12: false
        };
        
        const parsed_date = Date.parse(date);
        
        // If the date was parsed successfully we should update the string
        if (!isNaN(parsed_date)) {
            return new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
        }
    }
    return "";
};


export const deepcopy = data => JSON.parse(JSON.stringify(data));