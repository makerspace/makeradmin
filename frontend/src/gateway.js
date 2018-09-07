import {showError, showPermissionDenied} from "./message";
import * as auth from "./auth";
import * as _ from "underscore";


export function get({url, params = {}}) {
    const options = {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken()
        }
    };

    url = config.apiBasePath + url + '?' + _.map(params, (v, k) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
    
    return fetch(url, options)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            
            if (response.status === 401) {
                showPermissionDenied();
                return null;
            }
            
            throw new Error(response.status + " " + response.statusText);
        })
        .catch(error => {
            showError(
                "<h2>Error</h2>Error when getting data from server:<br><br>" +
                "<pre>" + error + "</pre>"
            );
        });
}

export function del({url}) {
    const options = {
        method: 'DELETE',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken()
        }
    };
    
    url = config.apiBasePath + url;
    
    return fetch(url, options)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            
            if (response.status === 401) {
                showPermissionDenied();
                return null;
            }
            
            throw new Error(response.status + " " + response.statusText);
        })
        .then(data => {
            if ("deleted" === data.status) {
                return data;
            }
            throw new Error(JSON.stringify(data));
        })
        .catch(error => {
            showError(
                "<h2>Error</h2>"+
                "Error when deleting:<br><br>" +
                "<pre>" + error + "</pre>"
            );
        });
}
