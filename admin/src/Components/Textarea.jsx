import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";

const Textarea = (props) => {
    const [value, setValue] = useState("");
    const [selected, setSelected] = useState(false);
    const [isDirty, setIsDirty] = useState(false);

    useEffect(() => {
        const { model, name } = props;

        const handleModelChange = () => {
            setValue(model[name] === null ? "" : model[name]);
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
        rows,
    } = props;

    const classes = classNames(name, {
        "uk-form-row": formrow,
        selected: selected,
        changed: isDirty,
    });

    const textarea = (
        <textarea
            id={name}
            name={name}
            placeholder={placeholder}
            className="uk-width-1-1"
            value={value}
            disabled={disabled}
            tabIndex={tabIndex}
            rows={rows || 8}
            onChange={(e) => (model[name] = e.target.value)}
            onFocus={() => setSelected(true)}
            onBlur={() => setSelected(false)}
        />
    );

    return (
        <div className={classes}>
            <label className="uk-form-label" htmlFor={name}>
                {title}
            </label>
            <div className="uk-form-controls">
                {icon ? (
                    <div className="uk-form-icon">
                        <i className={"uk-icon-" + icon} />
                        {textarea}
                    </div>
                ) : (
                    textarea
                )}
            </div>
        </div>
    );
};

Textarea.defaultProps = {
    formrow: true,
};

export default Textarea;
