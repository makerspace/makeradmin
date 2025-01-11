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
    const maybe_form_icon = form ? "uk-form-icon" : "";

    if (isExtraIconName(name)) {
        return (
            <span className={maybe_form_icon + " uk-icon"}>
                {extraIcons[name]}
            </span>
        );
    }

    return <span className={maybe_form_icon} uk-icon={"icon: " + name} />;
}
