import React from "react";
import { extraIconNames, extraIcons, isExtraIconName } from "./extra-icons";
import { UiKitIconName } from "./uikit";

export type IconProps = {
    icon: UiKitIconName | extraIconNames;
    form?: boolean;
};

export default function Icon({
    icon: name,
    form = false,
}: IconProps): React.ReactElement {
    if (isExtraIconName(name)) {
        return (
            <span className={form ? "uk-form-icon" : "uk-icon"}>
                {extraIcons[name]}
            </span>
        );
    }

    return (
        <span
            className={form ? "uk-form-icon" : null}
            uk-icon={"icon: " + name}
        />
    );
}
