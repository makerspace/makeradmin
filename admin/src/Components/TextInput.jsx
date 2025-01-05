import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";
import * as _ from "underscore";
import Icon from "./icons";

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
        tabIndex,
        type,
        autoComplete,
    } = props;

    const classes = classNames(name, {
        "form-row": true,
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
            {title && (
                <label className="uk-form-label" htmlFor={name}>
                    {title}
                </label>
            )}
            {icon ? (
                <div className="uk-inline">
                    <Icon form icon={icon} />
                    {input}
                </div>
            ) : (
                input
            )}
        </div>
    );
};

TextInput.defaultProps = {
    autoComplete: "off",
};

export default TextInput;
