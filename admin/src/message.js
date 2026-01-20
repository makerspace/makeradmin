import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import UIkit from "uikit";

export function showPermissionDenied(responseData) {
    let message;
    if (typeof responseData === "string") {
        // Legacy: responseData is already a formatted message string
        message = responseData;
    } else if (responseData && responseData.what) {
        // New: responseData contains the missing permission in the 'what' field
        message =
            "<h2>Permission Denied</h2>" +
            "You do not have the required permission: <strong>" +
            responseData.what +
            "</strong><br><br>" +
            "Please contact an administrator if you believe you should have access to this resource.";
    } else if (responseData && responseData.message) {
        // Fallback: use the message from the response
        message = "<h2>Permission Denied</h2>" + responseData.message;
    } else {
        // Default message
        message =
            "<h2>Error</h2>" +
            "You are unauthorized to use this API resource. " +
            "This could be because one of the following reasons:<br>" +
            "<br>1) You have been logged out from the API" +
            "<br>2) You do not have permissions to access this resource";
    }
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

function jsxToString(jsx) {
    // Note that the JSX has to be rendered already when calling this function.
    // I.e. any side effects in the components have to be completed first.
    const div = document.createElement("div");
    const root = createRoot(div);
    flushSync(() => {
        root.render(jsx);
    });
    return div.innerHTML;
}

export function showError(message) {
    message = message || "<h2>Error</h2>" + "Unknown error.";
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

export function showSuccess(message) {
    UIkit.notification(message, { timeout: 0, status: "success" });
}

export function confirmModal(content) {
    return UIkit.modal.confirm(jsxToString(content));
}

export function notifySuccess(message) {
    UIkit.notification(message, { status: "success" });
}

export function notifyError(message) {
    UIkit.notification(message, { status: "danger" });
}
