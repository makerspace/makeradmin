interface Window {
    get: (params: {
        url: string;
        params: { [key: string]: string | number | boolean };
        data?: object | null;
        options: RequestInit;
        errorMessage: string;
        expectedDataStatus?: string | null;
    }) => Promise<any>;
}

declare var config: {
    apiBasePath: string;
    apiVersion: string;
    pagination: {
        pageSize: number;
    };
};
