import React, { useEffect } from "react";
import { get, RequestParams } from "../gateway";

export function useJson<T>(params: RequestParams): {
    data: T | null;
    isLoading: boolean;
    error: any;
} {
    const [data, setData] = React.useState<T | null>(null);
    const [isLoading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    useEffect(() => {
        setLoading(true);
        get(params)
            .then((data) => {
                setData(data.data as T);
                setLoading(false);
                setError(null);
            })
            .catch((err) => {
                setError(err);
                setData(null);
                setLoading(false);
            });
    }, [params.url, ...Object.values(params.params ?? {})]);

    return {
        data,
        isLoading,
        error,
    };
}
