import React, { useEffect, useMemo, useState } from "react";
import DatePeriod from "../Models/DatePeriod";
import { utcToday } from "../utils";
import DatePeriodInput from "./DatePeriodInput";
import Icon from "./icons";

const CategoryPeriodsInput = ({ categoryPeriods, showHistoric }) => {
    const [periods, setPeriods] = useState([]);

    useEffect(() => {
        const unsubscribe = categoryPeriods.subscribe(() => {
            // Must create a new array to force re-render
            setPeriods(Array.from(categoryPeriods.periods));
        });

        return () => {
            unsubscribe();
        };
    }, [categoryPeriods]);

    const { category } = categoryPeriods;

    const today = utcToday();
    const categoryTitle = {
        labaccess: "Labaccess",
        special_labaccess: "Access till lokalen (styrelsen etc)",
        membership: "Medlemsskap",
    };

    const templates = useMemo(
        () => [
            { label: "1 day", start: today, end: today },
            {
                label: "1 month",
                start: today,
                end: new Date(
                    today.getFullYear(),
                    today.getMonth() + 1,
                    today.getDate(),
                ),
            },
            {
                label: "3 months",
                start: today,
                end: new Date(
                    today.getFullYear(),
                    today.getMonth() + 3,
                    today.getDate(),
                ),
            },
            {
                label: "6 months",
                start: today,
                end: new Date(
                    today.getFullYear(),
                    today.getMonth() + 6,
                    today.getDate(),
                ),
            },
            {
                label: "1 year",
                start: today,
                end: new Date(
                    today.getFullYear() + 1,
                    today.getMonth(),
                    today.getDate(),
                ),
            },
            {
                label: "To end of year",
                start: today,
                end: new Date(today.getFullYear(), 11, 31),
            },
        ],
        [],
    );

    return (
        <div>
            <h4 className="uk-margin-top">{categoryTitle[category]}</h4>
            {periods.map((p) => {
                if (!showHistoric && p.end < today) {
                    return null;
                }
                return (
                    <div key={p.id} className="uk-flex uk-flex-middle">
                        <DatePeriodInput
                            period={p}
                            highlightChanges={true}
                            templates={templates}
                        />
                        &nbsp;
                        <a
                            onClick={() => categoryPeriods.remove(p)}
                            className="removebutton"
                        >
                            <Icon icon="trash" />
                        </a>
                    </div>
                );
            })}
            <button
                type="button"
                style={{ marginTop: "2px" }}
                className="uk-button uk-button-small uk-button-primary"
                onClick={() => {
                    const period = new DatePeriod();
                    period.start = utcToday();
                    period.end = utcToday();
                    categoryPeriods.add(period);
                }}
            >
                Lägg till period
            </button>
        </div>
    );
};

export default CategoryPeriodsInput;
