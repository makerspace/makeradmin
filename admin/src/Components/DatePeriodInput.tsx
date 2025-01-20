import React, { useEffect, useRef, useState } from "react";
import { DayPicker } from "react-day-picker";
import DatePeriod from "../Models/DatePeriod";
import { formatUtcDate, parseUtcDate, utcToday } from "../utils";

type DateRangeTemplate = {
    label: string;
    start: Date;
    end: Date;
};

const DayPickerInput = <T extends { label: string }>({
    inputId,
    isValid,
    isChanged,
    value,
    onChange,
    inputStyle,
    tabindex,
    templates,
    onSelectedTemplate,
}: {
    inputId: string;
    isValid: boolean;
    isChanged: boolean;
    tabindex?: number;
    value: Date | null;
    onChange: (date: Date | undefined) => void;
    inputStyle?: React.CSSProperties;
    templates: T[];
    onSelectedTemplate: (template: T) => void;
}) => {
    const dialogRef = useRef<HTMLDialogElement>(null);

    // Hold the month in state to control the calendar when the input changes
    const [month, setMonth] = useState(value ?? new Date());
    const [inputValue, setInputValue] = useState(
        value ? formatUtcDate(value) : "",
    );

    // Hold the dialog visibility in state
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    useEffect(() => {
        if (value) {
            const utcDate = new Date(
                Date.UTC(
                    value.getFullYear(),
                    value.getMonth(),
                    value.getDate(),
                ),
            );
            setInputValue(formatUtcDate(utcDate));
            setMonth(utcDate);
            console.log(value, utcDate);
        }
    }, [value]);

    // Hook to handle the body scroll behavior and focus trapping.
    useEffect(() => {
        const handleBodyScroll = (isOpen: boolean) => {
            document.body.style.overflow = isOpen ? "hidden" : "";
        };
        if (!dialogRef.current) return;
        if (isDialogOpen) {
            handleBodyScroll(true);
            dialogRef.current.showModal();
        } else {
            handleBodyScroll(false);
            dialogRef.current.close();
        }
        return () => {
            handleBodyScroll(false);
        };
    }, [isDialogOpen]);

    const handleDayPickerSelect = (date: Date | undefined) => {
        if (!date) {
            // Ignore
            // This can happen when clicking on the same date twice
            // setInputValue("");
            // onChange(undefined);
        } else {
            const utcDate = new Date(
                Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()),
            );
            onChange(utcDate);
            setMonth(utcDate);
            setInputValue(formatUtcDate(utcDate));
        }
        dialogRef.current?.close();
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value); // keep the input value in sync

        const parsedDate = parseUtcDate(e.target.value);

        if (parsedDate !== null) {
            onChange(parsedDate);
            setMonth(parsedDate);
        } else {
            onChange(undefined);
        }
    };

    return (
        <>
            <input
                style={inputStyle}
                id={inputId}
                type="text"
                value={inputValue}
                placeholder="YYYY-MM-DD"
                size={10}
                tabIndex={tabindex}
                className={
                    "uk-input" +
                    (isValid
                        ? isChanged
                            ? " changed-date"
                            : ""
                        : " uk-form-danger")
                }
                onChange={handleInputChange}
            />
            <div data-uk-dropdown="pos: bottom-center; delay-hide: 100">
                <div className="uk-flex">
                    {templates.length > 0 && (
                        <ul className="uk-list uk-text-right date-period-templates">
                            {templates.map((template) => (
                                <li key={template.label}>
                                    <a
                                        className="uk-link-muted"
                                        onClick={() =>
                                            onSelectedTemplate(template)
                                        }
                                    >
                                        {template.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    )}
                    <DayPicker
                        month={month}
                        onMonthChange={setMonth}
                        timeZone="UTC"
                        mode="single"
                        selected={value || new Date()}
                        onSelect={handleDayPickerSelect}
                    />
                </div>
            </div>
        </>
    );
};

const DatePeriodInput = ({
    period,
    highlightChanges = false,
    templates = [],
}: {
    period: DatePeriod & { start: Date | null; end: Date | null };
    highlightChanges?: boolean;
    templates?: DateRangeTemplate[];
}) => {
    const [start, setStart] = useState(period.start || null);
    const [end, setEnd] = useState(period.end || null);

    useEffect(() => {
        const unsubscribe = period.subscribe(() => {
            setStart(period.start);
            setEnd(period.end);
        });

        return () => {
            unsubscribe();
        };
    }, [period]);

    const handleDayChange = (date: Date | undefined, type: "start" | "end") => {
        if (type === "start") {
            period.start = date || null;
            setStart(date || null);
        } else if (type === "end") {
            period.end = date || null;
            setEnd(date || null);
        }
    };

    const onSelectedTemplate = (template: DateRangeTemplate) => {
        // Ensure that the dates are UTC dates at midnight
        const utcStart = new Date(
            Date.UTC(
                template.start.getFullYear(),
                template.start.getMonth(),
                template.start.getDate(),
            ),
        );
        const utcEnd = new Date(
            Date.UTC(
                template.end.getFullYear(),
                template.end.getMonth(),
                template.end.getDate(),
            ),
        );
        handleDayChange(utcStart, "start");
        handleDayChange(utcEnd, "end");
    };

    const today = utcToday();
    const historicStyle = { color: "darkcyan" };

    return (
        <>
            {/* Input for start date */}
            <span>
                <DayPickerInput
                    inputStyle={{
                        marginTop: "2px",
                        ...(start && start < today && historicStyle),
                    }}
                    inputId="start"
                    isValid={period.isValid("start")}
                    isChanged={highlightChanges && period.isDirty("start")}
                    value={start}
                    onChange={(date) => handleDayChange(date, "start")}
                    tabindex={600}
                    templates={templates}
                    onSelectedTemplate={onSelectedTemplate}
                />
            </span>
            &nbsp;-&nbsp;
            {/* Input for end date */}
            <span>
                <DayPickerInput
                    inputStyle={{
                        marginTop: "2px",
                        ...(end && end < today && historicStyle),
                    }}
                    inputId="end"
                    tabindex={601}
                    isValid={period.isValid("end")}
                    isChanged={highlightChanges && period.isDirty("end")}
                    value={end}
                    onChange={(date) => handleDayChange(date, "end")}
                    templates={templates}
                    onSelectedTemplate={onSelectedTemplate}
                />
            </span>
        </>
    );
};

export const commonPeriodTemplates = (now: Date): DateRangeTemplate[] => {
    return [
        {
            label: "Last 30 days",
            start: new Date(now.getTime() - 1000 * 60 * 60 * 24 * 30),
            end: now,
        },
        {
            label: "Last 90 days",
            start: new Date(now.getTime() - 1000 * 60 * 60 * 24 * 90),
            end: now,
        },
        {
            label: "Last 365 days",
            start: new Date(now.getTime() - 1000 * 60 * 60 * 24 * 365),
            end: now,
        },
        {
            label: "Last 5 years",
            start: new Date(
                now.getFullYear() - 5,
                now.getMonth(),
                now.getDate(),
            ),
            end: now,
        },
        {
            label: "Year to date",
            start: new Date(now.getFullYear(), 0, 1),
            end: now,
        },
    ];
};

export default DatePeriodInput;
