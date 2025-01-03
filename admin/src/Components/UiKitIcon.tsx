import React from "react";

// See ui-kit documentation for the list of all available icons
// https://getuikit.com/docs/icon
type UiKitIconName = "trash";

type IconProps = {
    icon: UiKitIconName;
};

const raise_to_align_with_text: React.CSSProperties = {
    display: "inline-block",
    transform: "translateY(-2px)", // Make icon vertically aligned with text
};

export default function UiKitIcon({ icon }: IconProps): React.ReactElement {
    return <span uk-icon={"icon: " + icon} style={raise_to_align_with_text} />;
}
