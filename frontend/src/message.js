import UIkit from 'uikit';


export function showPermissionDenied(message) {
    message = message || (
        "<h2>Error</h2>" +
        "You are unauthorized to use this API resource. " +
        "This could be because one of the following reasons:<br>" +
        "<br>1) You have been logged out from the API" +
        "<br>2) You do not have permissions to access this resource"
    );
    UIkit.notify(message, {timeout: 0, status: "danger"});
}


export function showError(message) {
    message = message || (
        "<h2>Error</h2>" +
        "Unknown error."
    );
    UIkit.notify(message, {timeout: 0, status: "danger"});
}
