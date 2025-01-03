import React from "react";

// See ui-kit documentation for the list of all available icons
// https://getuikit.com/docs/icon
type UiKitIconName =
    | "calendar"
    | "cart"
    | "check"
    | "chevron-down"
    | "chevron-up"
    | "cog"
    | "commenting"
    | "eye-slash"
    | "home"
    | "lock"
    | "plus"
    | "plus-circle"
    | "mail"
    | "tag"
    | "trash"
    | "refresh"
    | "search"
    | "settings"
    | "user";

type IconProps = {
    icon: UiKitIconName;
    form?: boolean;
};

const raise_to_align_with_text: React.CSSProperties = {
    display: "inline-block",
    transform: "translateY(-2px)", // Make icon vertically aligned with text
};

export function SaveIcon(): React.ReactElement {
    return (
        <span
            className="uk-icon"
            uk-icon="save"
            style={raise_to_align_with_text}
        >
            <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                data-svg="save"
            >
                <path fill="#000" d="M12 2h1v3h-1z"></path>
                <path
                    d="M15.885 1.5H1.5v17h17v-14l-2.615-3z"
                    stroke="#000"
                ></path>
                <path
                    d="M5.5 1.5v4h8v-4M4.5 18.5v-10h11v10M7 11.5h6M7 13.5h6M7 15.5h6"
                    stroke="#000"
                ></path>
                <path fill="#000" d="M6 2h4v3H6z"></path>
            </svg>
        </span>
    );
}

export default function UiKitIcon({
    icon,
    form = false,
}: IconProps): React.ReactElement {
    if (form) {
        return (
            <span
                className={form ? "uk-form-icon" : null}
                uk-icon={"icon: " + icon}
            />
        );
    }

    return <span uk-icon={"icon: " + icon} style={raise_to_align_with_text} />;
}
