interface Window {
    get: (params: {
        url: string;
        params: { [key: string]: string };
        data: object | undefined;
        options: RequestInit;
        errorMessage: string;
        expectedDataStatus: string | undefined;
    }) => Promise<any>;
}

declare var config: {
    apiBasePath: string;
    apiVersion: string;
    pagination: {
        pageSize: number;
    };
};
