import React from "react";

export default <T extends string | number>({
    value,
    onChange,
    options,
    label,
}: {
    value: T;
    onChange: (value: T) => void;
    options: readonly T[];
    label: (v: T) => string;
}) => {
    return (
        <div className="uk-button-group">
            {options.map((g) => (
                <button
                    key={g}
                    onClick={() => onChange(g)}
                    className={`uk-button uk-button-small uk-button-${
                        g == value ? "primary" : "default"
                    }`}
                >
                    {label(g)}
                </button>
            ))}
        </div>
    );
};
