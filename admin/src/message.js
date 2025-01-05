import UIkit from "uikit";

export function showPermissionDenied(message) {
    message =
        message ||
        "<h2>Error</h2>" +
            "You are unauthorized to use this API resource. " +
            "This could be because one of the following reasons:<br>" +
            "<br>1) You have been logged out from the API" +
            "<br>2) You do not have permissions to access this resource";
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

export function showError(message) {
    message = message || "<h2>Error</h2>" + "Unknown error.";
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

export function showSuccess(message) {
    UIkit.notification(message, { timeout: 0, status: "success" });
}

export function confirmModal(message) {
    return UIkit.modal.confirm(message);
}

export function notifySuccess(message) {
    UIkit.notification(message, { status: "success" });
}
