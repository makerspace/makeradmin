import React, { useEffect, useState } from "react";
import DatePeriod from "../Models/DatePeriod";
import { utcToday } from "../utils";
import DatePeriodInput from "./DatePeriodInput";
import Icon from "./icons";

const CategoryPeriodsInput = ({ categoryPeriods, showHistoric }) => {
    const [periods, setPeriods] = useState([]);

    useEffect(() => {
        const unsubscribe = categoryPeriods.subscribe(() => {
            setPeriods(categoryPeriods.periods);
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

    return (
        <div>
            <h4 className="uk-margin-top">{categoryTitle[category]}</h4>
            {periods.map((p) => {
                if (!showHistoric && p.end < today) {
                    return null;
                }
                return (
                    <div key={p.id}>
                        <DatePeriodInput period={p} />
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
