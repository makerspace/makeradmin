import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";
import { dateTimeToStr } from "../utils";

const DateTimeInput = ({ model, name, title, icon, placeholder }) => {
    const [value, setValue] = useState("");

    useEffect(() => {
        const unsubscribe = model.subscribe(() => {
            setValue(dateTimeToStr(model[name]));
        });

        return () => {
            unsubscribe();
        };
    }, [model, name]);

    const classes = classNames(name, {
        "form-row": true,
        selected: false,
        changed: false,
    });

    const input = (
        <input
            type="text"
            name={name}
            id={name}
            disabled={true}
            value={value}
            placeholder={placeholder}
            className="uk-form-width-large"
        />
    );

    return (
        <div className={classes}>
            <label htmlFor={name} className="uk-form-label">
                {title}
            </label>
            <div className="uk-form-controls">
                {icon ? (
                    <div className="uk-form-icon">
                        <i className={"uk-icon-" + icon} />
                        {input}
                    </div>
                ) : (
                    input
                )}
            </div>
        </div>
    );
};

export default DateTimeInput;
