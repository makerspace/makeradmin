import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";

const CheckboxInput = ({
    model,
    name,
    title,
    icon,
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
        "uk-form-row": formrow,
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

CheckboxInput.defaultProps = {
    formrow: true,
    label: true,
};

export default CheckboxInput;
