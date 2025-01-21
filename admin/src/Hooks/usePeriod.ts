import DatePeriod from "Models/DatePeriod";
import React, { useEffect, useMemo } from "react";

export const usePeriod = (initial?: { start?: Date; end?: Date }) => {
    const [version, setVersion] = React.useState(0);
    const period = useMemo(() => {
        const start = new Date();
        start.setDate(start.getDate() - 365);
        const period = new DatePeriod({ start, end: new Date() });
        if (initial?.start) period.start = initial.start;
        if (initial?.end) period.end = initial.end;
        return period;
    }, []);
    const [lastValidPeriod, setLastValidPeriod] = React.useState({
        start: period.start,
        end: period.end,
    });
    useEffect(() => {
        const unsub = period.subscribe(() => {
            // Dirty to force a re-render
            setVersion((v) => v + 1);
            if (period.isValid()) {
                setLastValidPeriod({ start: period.start, end: period.end });
            }
        });
        return () => {
            unsub();
        };
    }, [period]);

    return { period, lastValidPeriod };
};
