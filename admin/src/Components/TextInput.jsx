import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";
import * as _ from "underscore";

const TextInput = (props) => {
    const [value, setValue] = useState(null);
    const [selected, setSelected] = useState(false);
    const [isDirty, setIsDirty] = useState(false);

    useEffect(() => {
        const { model, name } = props;

        const handleModelChange = () => {
            setValue(model[name] === "" ? null : model[name]);
            setIsDirty(model.isDirty(name));
        };

        const unsubscribe = model.subscribe(handleModelChange);

        return () => {
            unsubscribe();
        };
    }, [props.model, props.name]);

    const {
        model,
        name,
        title,
        icon,
        disabled,
        placeholder,
        formrow,
        tabIndex,
        type,
        label,
        autoComplete,
    } = props;

    const classes = classNames(name, {
        "uk-form-row": formrow,
        selected: selected,
        changed: isDirty,
    });

    const input = (
        <input
            id={name}
            name={name}
            placeholder={placeholder}
            className="uk-input uk-width-1-1"
            value={_.isNull(value) ? "" : value}
            disabled={disabled}
            type={type || "text"}
            tabIndex={tabIndex}
            onChange={(event) =>
                (model[name] =
                    event.target.value === "" ? null : event.target.value)
            }
            onFocus={() => setSelected(true)}
            onBlur={() => setSelected(false)}
            autoComplete={autoComplete}
        />
    );

    return (
        <div className={classes}>
            {label ? (
                <label className="uk-form-label" htmlFor={name}>
                    {title}
                </label>
            ) : null}
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

TextInput.defaultProps = {
    formrow: true,
    label: true,
    autoComplete: "off",
};

export default TextInput;
