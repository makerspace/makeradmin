import { get, RequestParams } from "gateway";
import React, { useEffect } from "react";

export type CacheGetter<T, U> = (key: T) => U | null;

export type DataCache<T, U> = {
    cache: CacheGetter<T, U>;
    version: number;
    isLoading: boolean;
};

type CacheItem<T> = {
    global_cache_key: any;
    pending: boolean;
    value: T | null;
};

export function useDataCache<T, U>(
    items: T[],
    cache_key: any,
    url: (item: T) => RequestParams,
): DataCache<T, U> {
    const cache = React.useRef<Map<T, CacheItem<U>>>(new Map());
    const [version, setVersion] = React.useState(0);
    const [pending, setPending] = React.useState(0);

    useEffect(() => {
        for (const item of items) {
            const existing = cache.current.get(item);
            const needsUpdate =
                existing === undefined ||
                (existing.global_cache_key != cache_key && !existing.pending);
            if (needsUpdate) {
                cache.current.set(item, {
                    global_cache_key: cache_key,
                    pending: true,
                    value: existing?.value ?? null,
                });
                setPending((p) => p + 1);
                get(url(item)).then((data) => {
                    cache.current.set(item, {
                        global_cache_key: cache_key,
                        pending: false,
                        value: data.data as U,
                    });
                    setVersion((v) => v + 1);
                    setPending((p) => p - 1);

                    // This request may have been done with an outdated cache key.
                    // But since we set pending, this effect will re-run and start a new request, if necessary.
                });
            }
        }
    }, [items, cache_key, pending]);

    return {
        cache: (key: T) => cache.current.get(key)?.value ?? null,
        version,
        isLoading: pending > 0,
    };
}
