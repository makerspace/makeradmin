import classNames from "classnames";
import React, { useEffect, useState, forwardRef } from "react";

interface TextareaProps {
    model: any;
    name: string;
    title: string;
    disabled?: boolean;
    placeholder?: string;
    tabIndex?: number;
    rows?: number;
    onChange?: () => void;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    (props, ref) => {
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
            disabled,
            placeholder,
            tabIndex,
            rows,
            onChange,
        } = props;

        const classes = classNames(name, {
            "form-row": true,
            selected: selected,
            changed: isDirty,
        });

        const textarea = (
            <textarea
                ref={ref}
                id={name}
                name={name}
                placeholder={placeholder}
                className="uk-width-1-1"
                value={value}
                disabled={disabled}
                tabIndex={tabIndex}
                rows={rows || 8}
                onChange={(e) => {
                    model[name] = e.target.value;
                    onChange?.();
                }}
                onFocus={() => setSelected(true)}
                onBlur={() => setSelected(false)}
            />
        );

        return (
            <div className={classes}>
                <label className="uk-form-label" htmlFor={name}>
                    {title}
                </label>
                <div className="uk-form-controls">{textarea}</div>
            </div>
        );
    },
);

Textarea.displayName = "Textarea";

export default Textarea;
