import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";

const CheckboxInput = ({
    model,
    name,
    title,
    disabled,
    formrow,
    tabIndex,
    label,
}) => {
    const [value, setValue] = useState(false);
    const [isDirty, setIsDirty] = useState(false);

    useEffect(() => {
        const unsubscribe = model.subscribe(() => {
            setValue(model[name] === "" ? false : model[name]);
            setIsDirty(model.isDirty(name));
        });

        return () => {
            unsubscribe();
        };
    }, [model, name]);

    const classes = classNames(name, {
        "form-row": formrow,
        changed: isDirty,
    });

    const handleChange = () => {
        model[name] = !model[name];
    };

    const input = (
        <input
            id={name}
            name={name}
            className=""
            checked={value}
            disabled={disabled}
            type="checkbox"
            tabIndex={tabIndex}
            onChange={handleChange}
        />
    );

    return (
        <div className={classes}>
            {label && (
                <label className="uk-form-label" htmlFor={name}>
                    {title}
                </label>
            )}
            <div className="uk-form-controls">{input}</div>
        </div>
    );
};

CheckboxInput.defaultProps = {
    formrow: true,
    label: true,
};

export default CheckboxInput;
