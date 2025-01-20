import * as _ from "underscore";

export const assert = (expression: any) => console.assert(expression);

const utcDateFormat = Intl.DateTimeFormat("sv-SE", {
    timeZone: "UTC",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
});

export const formatUtcDate = (date: Date) => utcDateFormat.format(date);

export const parseUtcDate = (str: string) => {
    if (/\d{4}-\d{2}-\d{2}/.test(str)) {
        const d = new Date(str + "T00:00:00.000Z");
        if (isNaN(d.getTime())) {
            return null;
        }
        return d;
    }
    return null;
};

export const utcToday = () => {
    const d = new Date();
    d.setUTCHours(0, 0, 0, 0);
    return d;
};

export const addToDate = (date: Date, millis: number) =>
    new Date(date.getTime() + millis);

// Parse and format date string.
export const dateToStr = (date: string) => {
    if (!_.isEmpty(date)) {
        const options: Intl.DateTimeFormatOptions = {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour12: false,
        };

        const parsed_date = Date.parse(date);

        if (!isNaN(parsed_date)) {
            return new Intl.DateTimeFormat("sv-SE", options).format(
                parsed_date,
            );
        }
    }
    return "";
};

// Parse and format datetime string.
export const dateTimeToStr = (date: string) => {
    if (!_.isEmpty(date)) {
        const options: Intl.DateTimeFormatOptions = {
            year: "numeric",
            month: "numeric",
            day: "numeric",
            hour: "numeric",
            minute: "numeric",
            second: "numeric",
            hour12: false,
        };

        const parsed_date = Date.parse(date);

        if (!isNaN(parsed_date)) {
            return new Intl.DateTimeFormat("sv-SE", options).format(
                parsed_date,
            );
        }
    }
    return "";
};

export const sum = <T>(items: T[], value: (item: T) => number) => {
    let s = 0;
    for (const item of items) {
        s += value(item);
    }
    return s;
};

export const copyArray = <T>(src: T[], dest: T[]) => {
    for (let i = 0; i < src.length; i++) {
        dest[i] = src[i]!;
    }
};

export const deepcopy = <T>(data: T): T => JSON.parse(JSON.stringify(data));
