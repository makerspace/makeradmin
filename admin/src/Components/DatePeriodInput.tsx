import React, { useEffect, useRef, useState } from "react";
import { DayPicker } from "react-day-picker";
import DatePeriod from "../Models/DatePeriod";
import { formatUtcDate, parseUtcDate, utcToday } from "../utils";

const DayPickerInput = ({
    inputId,
    isValid,
    isChanged,
    value,
    onChange,
    inputStyle
}: {
    inputId: string
    isValid: boolean,
    isChanged: boolean,
    value: Date | null,
    onChange: (date: Date | undefined) => void,
    inputStyle?: React.CSSProperties,
}) => {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const dialogId = "dialog-" + inputId;
    const headerId = "header-" + inputId;

    // Hold the month in state to control the calendar when the input changes
    const [month, setMonth] = useState(value ?? new Date());
    const [inputValue, setInputValue] = useState(value ? formatUtcDate(value) : "");

    // Hold the dialog visibility in state
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    // Function to toggle the dialog visibility
    const toggleDialog = () => setIsDialogOpen(!isDialogOpen);

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
            const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
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

    return <>
        <input
            style={inputStyle}
            id={inputId}
            type="text"
            value={inputValue}
            placeholder="YYYY-MM-DD"
            size={10}
            className={"uk-input" + (isValid ? (isChanged ? " changed-date" : "") : " uk-form-danger")}
            onChange={handleInputChange}
            data-uk-dropdown
        />
        <button
            type="button"
            className="uk-button uk-button-default"
            style={{ fontSize: "inherit" }}
            onClick={toggleDialog}
            aria-controls="dialog"
            aria-haspopup="dialog"
            aria-expanded={isDialogOpen}
            aria-label="Open calendar to choose date"
        >📆</button>
        <dialog
            role="dialog"
            ref={dialogRef}
            id={dialogId}
            aria-modal
            aria-labelledby={headerId}
            onClose={() => setIsDialogOpen(false)}
        >
            <DayPicker
                month={month}
                onMonthChange={setMonth}
                timeZone="UTC"
                autoFocus
                mode="single"
                selected={value || new Date()}
                onSelect={handleDayPickerSelect}
            />
        </dialog>
    </>
}

const DatePeriodInput = ({ period }: { period: DatePeriod & { start: Date | null, end: Date | null } }) => {
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

    const today = utcToday();
    const historicStyle = { color: "darkcyan" };

    return (
        <span>
            {/* Input for start date */}
            <span>
                <DayPickerInput
                    inputStyle={{
                        marginTop: "2px",
                        ...(start && start < today && historicStyle),
                    }}
                    inputId="start"
                    isValid={period.isValid("start")}
                    isChanged={period.isDirty("start")}
                    value={start}
                    onChange={(date) => handleDayChange(date, "start")}
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
                    isValid={period.isValid("end")}
                    isChanged={period.isDirty("end")}
                    value={end}
                    onChange={(date) => handleDayChange(date, "end")}
                />
            </span>
        </span>
    );
};

export default DatePeriodInput;


