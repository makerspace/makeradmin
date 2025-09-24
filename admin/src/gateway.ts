import * as _ from "underscore";
import auth from "./auth";
import { showError, showPermissionDenied } from "./message";

const handleError = (message: string) => (error: Error) => {
    showError(
        "<h2>Error</h2>" +
            message +
            "<br>" +
            "<pre>" +
            error.message +
            "</pre>",
    );
    return Promise.reject(null);
};

export function request({
    url,
    params,
    data,
    options,
    errorMessage,
    expectedDataStatus,
    allowedErrorCodes,
}: {
    url: string;
    params: { [key: string]: string | number | boolean | undefined };
    data: object | null | undefined;
    options: RequestInit;
    errorMessage: string;
    expectedDataStatus: string | null | undefined;
    allowedErrorCodes: number[] | undefined;
}): Promise<any> {
    const accessToken = auth.getAccessToken();

    let headers: { [key: string]: string } = {
        "Content-Type": "application/json; charset=UTF-8",
    };

    if (accessToken) {
        headers["Authorization"] = "Bearer " + accessToken;
    }

    options = Object.assign(
        { headers },
        data ? { body: JSON.stringify(data) } : {},
        options,
    );

    const urlParams = _.map(params, (v, k) =>
        v !== undefined
            ? encodeURIComponent(k) + "=" + encodeURIComponent(v)
            : "",
    ).join("&");
    url = config.apiBasePath + url + (urlParams ? "?" + urlParams : "");
    return fetch(url, options)
        .then((response) =>
            response
                .json()
                .then((responseData) => ({ response, responseData })),
        )
        .then(({ response, responseData }) => {
            if (
                response.ok &&
                (!expectedDataStatus ||
                    responseData.status === expectedDataStatus)
            ) {
                return responseData;
            }

            if (
                allowedErrorCodes !== undefined &&
                allowedErrorCodes.includes(response.status)
            ) {
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

            throw new Error(
                response.status +
                    " " +
                    response.statusText +
                    "\n" +
                    JSON.stringify(responseData, null, 2),
            );
        })
        .catch(handleError(errorMessage));
}

export type RequestParams = {
    url: string;
    params?: { [key: string]: string | number | boolean | undefined };
    data?: object | null;
    options?: RequestInit;
    errorMessage?: string;
    expectedDataStatus?: string | null;
    allowedErrorCodes?: number[];
};

export function get({
    url,
    params = {},
    data = null,
    options = { method: "GET" },
    errorMessage = "Error when getting data from server:",
    expectedDataStatus = null,
    allowedErrorCodes,
}: RequestParams): Promise<any> {
    return request({
        url,
        data,
        params,
        options,
        errorMessage,
        expectedDataStatus,
        allowedErrorCodes,
    });
}

export function post({
    url,
    params = {},
    data = null,
    options = { method: "POST" },
    errorMessage = "Error when creating:",
    expectedDataStatus = "created",
    allowedErrorCodes,
}: RequestParams): Promise<any> {
    return request({
        url,
        data,
        params,
        options,
        errorMessage,
        expectedDataStatus,
        allowedErrorCodes,
    });
}

export function put({
    url,
    params = {},
    data = null,
    options = { method: "PUT" },
    errorMessage = "Error when saving:",
    expectedDataStatus = "updated",
    allowedErrorCodes,
}: RequestParams): Promise<any> {
    return request({
        url,
        data,
        params,
        options,
        errorMessage,
        expectedDataStatus,
        allowedErrorCodes,
    });
}

export function del({
    url,
    params = {},
    data = null,
    options = { method: "DELETE" },
    errorMessage = "Error when deleting:",
    expectedDataStatus = "deleted",
    allowedErrorCodes,
}: RequestParams): Promise<any> {
    return request({
        url,
        data,
        params,
        options,
        errorMessage,
        expectedDataStatus,
        allowedErrorCodes,
    });
}

if (typeof window !== "undefined") {
    window.get = get;
}
