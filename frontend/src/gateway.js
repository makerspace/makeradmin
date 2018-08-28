import {showError, showPermissionDenied} from "./message";
import * as auth from "./auth";


export function get(url, success) {
    const options = {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken()
        }
    };
    
    fetch(config.apiBasePath + url, options)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            
            if (response.status === 401) {
                showPermissionDenied();
                return null;
            }
            
            showError(
                "<h2>Error</h2>" +
                "Received an unexpected result from the server:<br><br>" +
                response.status + " " + response.statusText);
            return null;
        })
        .then(success)
        .catch(error => {
            showError("<h2>Error</h2>Error while communicating with server:<br><br><pre>" + error + "</pre>");
        });
}
