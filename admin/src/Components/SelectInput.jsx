import classNames from "classnames/bind";
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { get } from "../gateway";

const SelectInput = (props) => {
    const [options, setOptions] = useState(props.options || []);
    const [isDirty, setIsDirty] = useState(false);
    const [value, setValue] = useState(null);

    useEffect(() => {
        if (props.dataSource) {
            let newOptions = [];
            if (props.nullOption) {
                newOptions = [props.nullOption];
            }
            get({ url: props.dataSource, params: { page_size: 0 } }).then(
                (data) => setOptions(newOptions.concat(data.data)),
                () => null,
            );
        }
    }, [props.dataSource, props.nullOption]);

    useEffect(() => {
        const handleModelChange = () => {
            setValue(
                props.model[props.name] === null ? "" : props.model[props.name],
            );
            setIsDirty(props.model.isDirty(props.name));
        };

        const unsubscribe = props.model.subscribe(handleModelChange);
        handleModelChange(); // Initialize state

        return () => {
            unsubscribe();
        };
    }, [props.model, props.name]);

    const classes = classNames(props.name, {
        changed: isDirty,
    });

    const select = (
        <Select
            id={props.name}
            name={props.name}
            className="uk-width-1-1"
            options={options}
            value={options.find((o) => o.id === value) || null}
            getOptionValue={props.getValue}
            getOptionLabel={props.getLabel}
            onChange={(o) => (props.model[props.name] = props.getValue(o))}
            isDisabled={!options.length}
        />
    );

    return (
        <div className={classes}>
            <label className="uk-form-label" htmlFor={props.name}>
                {props.title}
            </label>
            <div className="uk-form-controls">
                {props.icon ? (
                    <div className="uk-form-icon">
                        <i className={"uk-icon-" + props.icon} />
                        {select}
                    </div>
                ) : (
                    select
                )}
            </div>
        </div>
    );
};

export default SelectInput;
