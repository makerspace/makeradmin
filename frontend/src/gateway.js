import {showError, showPermissionDenied} from "./message";
import * as auth from "./auth";
import * as _ from "underscore";


// TODO Handle error better, use json response.


const handleResponse = response => {
    if (response.ok) {
        return response.json();
    }
    
    if (response.status === 401) {
        showPermissionDenied();
        return null;
    }
    
    throw new Error(response.status + " " + response.statusText);
};


const handleError = message => error => {
    showError(
        "<h2>Error</h2>"+
        message + "<br><br>" +
        "<pre>" + error + "</pre>"
    );
};



export function get({url, params = {}}) {
    const options = {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken()
        }
    };

    url = config.apiBasePath + url + '?' + _.map(params, (v, k) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
    
    return fetch(url, options)
        .then(handleResponse)
        .catch(handleError('Error when getting data from server:'));
}

export function post({url, data}) {
    const options = {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    };

    url = config.apiBasePath + url;

    return fetch(url, options)
        .then(handleResponse)
        .then(data => {
            if ("created" === data.status) {
                return data;
            }
            throw new Error(JSON.stringify(data));
        })
        .catch(handleError('Error when creating:'));
}

export function put({url, data}) {
    const options = {
        method: 'PUT',
        headers: {
            'Authorization': 'Bearer ' + auth.getAccessToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    };

    url = config.apiBasePath + url;

    return fetch(url, options)
        .then(handleResponse)
        .then(data => {
            if ("updated" === data.status) {
                return data;
            }
            throw new Error(JSON.stringify(data));
        })
        .catch(handleError('Error when saving:'));
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
        .then(handleResponse)
        .then(data => {
            if ("deleted" === data.status) {
                return data;
            }
            throw new Error(JSON.stringify(data));
        })
        .catch(handleError('Error when deleting:'));
}
