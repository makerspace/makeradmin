import {showError, showPermissionDenied} from "./message";
import * as auth from "./auth";
import * as _ from "underscore";


export function get({url, params = {}, success}) {
    const options = {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken()
        }
    };

    url = config.apiBasePath + url + '?' + _.map(params, (v, k) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
    
    fetch(url, options)
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
