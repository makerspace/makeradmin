import {showError, showPermissionDenied} from "./message";
import auth from "./auth";
import * as _ from "underscore";


const handleError = message => error => {
    showError(
        "<h2>Error</h2>"+
        message + "<br>" +
        "<pre>" + error.message + "</pre>"
    );
    return Promise.reject(null);
};


export function request({url, params, data, options, errorMessage, expectedDataStatus}) {
    
    options = Object.assign({headers: {'Authorization': 'Bearer ' + auth.getAccessToken(), 'Content-Type': 'application/json; charset=UTF-8'}},
                            data ? {body: JSON.stringify(data)} : {},
                            options);
    
    const urlParams = _.map(params, (v, k) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
    url = config.apiBasePath + url + (urlParams ? '?' + urlParams : '');
    return fetch(url, options)
        .then(response => response.json().then(responseData => ({response, responseData})))
        .then(({response, responseData}) => {
            if (response.ok && (!expectedDataStatus || responseData.status === expectedDataStatus)) {
                return responseData;
            }
            
            if (response.status === 401) {
                auth.logout();
                return null;
            }
            
            if (response.status === 403) {
                showPermissionDenied();
                return null;
            }
            
            throw new Error(response.status + " " + response.statusText + "\n" + JSON.stringify(responseData, null, 2));
        })
        .catch(handleError(errorMessage));
}
        

export function get({
                        url,
                        params = {},
                        data = null,
                        options = {method: 'GET'},
                        errorMessage = 'Error when getting data from server:',
                        expectedDataStatus = null,
                    })
{
    return request({url, data,params, options, errorMessage, expectedDataStatus});
}


export function post({
                        url,
                        params = {},
                        data = null,
                        options = {method: 'POST'},
                        errorMessage = 'Error when creating:',
                        expectedDataStatus = 'created',
                    })
{
    return request({url, data, params, options, errorMessage, expectedDataStatus});
}


export function put({
                        url,
                        params = {},
                        data = null,
                        options = {method: 'PUT'},
                        errorMessage = 'Error when saving:',
                        expectedDataStatus = 'updated',
                    })
{
    return request({url, data, params, options, errorMessage, expectedDataStatus});
}


export function del({
                        url,
                        params = {},
                        data = null,
                        options = {method: 'DELETE'},
                        errorMessage = 'Error when deleting:',
                        expectedDataStatus = 'deleted',
                    })
{
    return request({url, data, params, options, errorMessage, expectedDataStatus});
}


window.get = get;