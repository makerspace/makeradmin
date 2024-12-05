import React, { useEffect, useState } from "react";
import DayPickerInput from "react-day-picker/DayPickerInput";
import { formatUtcDate, parseUtcDate, utcToday } from "../utils";

const DatePeriodInput = ({ period }) => {
    const [start, setStart] = useState(period.start || null);
    const [end, setEnd] = useState(period.end || null);

    useEffect(() => {
        // Synchronize state with period on subscription updates
        const unsubscribe = period.subscribe(() => {
            setStart(period.start);
            setEnd(period.end);
        });

        return () => unsubscribe();
    }, [period]);

    const handleDayChange = (date, type) => {
        if (type === "start") {
            period.start = date || null;
            setStart(date || null);
        } else if (type === "end") {
            period.end = date || null;
            setEnd(date || null);
        }
    };

    const today = utcToday();
    const historicStyle = { color: "darkcyan" };

    return (
        <span>
            {/* Input for start date */}
            <span className={period.isDirty("start") ? "ma-changed" : ""}>
                <DayPickerInput
                    inputProps={{
                        size: 10,
                        className:
                            "uk-input" +
                            (period.isValid("start") ? "" : " uk-form-danger"),
                        style: {
                            marginTop: "2px",
                            ...(start && start < today && historicStyle),
                        },
                    }}
                    placeholder="YYYY-MM-DD"
                    value={start || ""}
                    parseDate={parseUtcDate}
                    formatDate={formatUtcDate}
                    onDayChange={(date) => handleDayChange(date, "start")}
                />
            </span>
            &nbsp;-&nbsp;
            {/* Input for end date */}
            <span className={period.isDirty("end") ? "ma-changed" : ""}>
                <DayPickerInput
                    inputProps={{
                        className:
                            "uk-input" +
                            (period.isValid("end") ? "" : " uk-form-danger"),
                        size: 10,
                        style: {
                            marginTop: "2px",
                            ...(end && end < today && historicStyle),
                        },
                    }}
                    placeholder="YYYY-MM-DD"
                    value={end || ""}
                    parseDate={parseUtcDate}
                    formatDate={formatUtcDate}
                    onDayChange={(date) => handleDayChange(date, "end")}
                />
            </span>
        </span>
    );
};

export default DatePeriodInput;
