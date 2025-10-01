import {
    labelExpiryDate,
    labelIsExpired,
    membership_t,
    UploadedLabel,
} from "frontend_common";
import { get, post } from "gateway";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActiveLogo } from "./ActiveLogo";
import { ExpiredLogo } from "./ExpiredLogo";
import QrCodeScanner from "./QrCodeScanner";

export interface LabelActionResponse {
    id: number;
    label: UploadedLabel;
}

const labelUrlRegex = /\/L\/([0-9_-]+)$/;

const ScanResultPopover = ({
    labelAction,
    membership,
    state,
}: {
    labelAction: LabelActionResponse;
    membership: membership_t;
    state: "active" | "fading-out";
}) => {
    const label = labelAction.label.label;
    const now = new Date();
    const expiresAt = labelExpiryDate(label, membership);
    const isExpired = labelIsExpired(now, label, membership);

    return (
        <div
            className={
                `box-terminator-popover` +
                (state === "fading-out" ? " fading-out" : "") +
                (isExpired ? " expired" : " active")
            }
        >
            <div>
                <div>{isExpired ? <ExpiredLogo /> : <ActiveLogo />}</div>
                {expiresAt && (
                    <div>
                        Expires&nbsp;
                        {(() => {
                            const expiresDate = new Date(expiresAt);
                            const now = new Date();
                            const diffMs =
                                expiresDate.getTime() - now.getTime();
                            if (diffMs < 0) return "in the past";
                            const diffDays = Math.floor(
                                diffMs / (1000 * 60 * 60 * 24),
                            );
                            if (diffDays > 0)
                                return `in ${diffDays} day${
                                    diffDays > 1 ? "s" : ""
                                }`;
                            const diffHours = Math.floor(
                                diffMs / (1000 * 60 * 60),
                            );
                            if (diffHours > 0)
                                return `in ${diffHours} hour${
                                    diffHours > 1 ? "s" : ""
                                }`;
                            const diffMinutes = Math.floor(
                                diffMs / (1000 * 60),
                            );
                            if (diffMinutes > 0)
                                return `in ${diffMinutes} minute${
                                    diffMinutes > 1 ? "s" : ""
                                }`;
                            return "soon";
                        })()}
                    </div>
                )}
                <a
                    href={labelAction.label.public_url}
                    className="uk-button uk-button-default"
                >
                    View
                </a>
            </div>
        </div>
    );
};

const LabelIdSearchPopover = ({
    onSelect,
    onClose,
}: {
    onSelect: (labelId: number) => void;
    onClose: () => void;
}) => {
    const [input, setInput] = useState("");
    const [results, setResults] = useState<
        { id: number; description: string; public_url: string }[]
    >([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (input.length === 0) {
            setResults([]);
            return;
        }
        setLoading(true);
        get({
            url: `/multiaccess/memberbooth/label/search/${input}`,
        })
            .then((res) => {
                setResults(res.data);
            })
            .finally(() => setLoading(false));
    }, [input]);

    return (
        <div className="label-id-search-popover">
            <button className="close-btn" onClick={onClose}>
                ×
            </button>
            <input
                type="tel"
                pattern="[0-9]*"
                inputMode="numeric"
                autoFocus
                placeholder="Enter label ID"
                value={input}
                onChange={(e) => setInput(e.target.value.replace(/\D/g, ""))}
                style={{ fontSize: "2em", width: "100%", marginBottom: "1em" }}
            />
            {loading && <div>Searching…</div>}
            <ul>
                {results.map((label) => (
                    <li key={label.id}>
                        <button
                            className="label-search-result"
                            onClick={() => onSelect(label.id)}
                        >
                            #{label.id} – {truncate(label.description, 24)}
                        </button>
                    </li>
                ))}
            </ul>
            {results.length === 0 && input.length > 0 && !loading && (
                <div>No matching labels</div>
            )}
        </div>
    );
};

function truncate(str: string, n: number) {
    return str.length > n ? str.slice(0, n - 1) + "…" : str;
}

const BoxTerminator = () => {
    // Ensure only a single request is in flight at any one time
    const isScanning = useRef(false);
    const [pendingScan, setPendingScan] = useState<string | null>(null);
    const [lastScanResult, setLastScanResult] = useState<
        {
            label: LabelActionResponse;
            membership: membership_t;
            state: "active" | "fading-out";
            timer: NodeJS.Timeout;
        }[]
    >([]);
    const nullTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const scanCache = useRef(
        new Map<
            string,
            { label: LabelActionResponse; membership: membership_t } | null
        >(),
    );
    const [showLabelIdSearch, setShowLabelIdSearch] = useState(false);

    const processScan = async (scannedString: string) => {
        // Check cache first
        if (scanCache.current.has(scannedString)) {
            const cachedLabel = scanCache.current.get(scannedString) ?? null;
            return cachedLabel;
        }

        let matchedId: number | null = null;
        try {
            const parsed = new URL(scannedString);
            const match = parsed.pathname.match(labelUrlRegex);
            if (match) {
                matchedId = parseInt(match[1]!);
            }
        } catch {
            // Not a URL
        }
        console.log(matchedId);
        let label: LabelActionResponse | null = null;
        let membership: membership_t | null = null;
        try {
            if (matchedId !== null) {
                const [observeRes, membershipRes] = await Promise.all([
                    post({
                        url: `/multiaccess/memberbooth/label/${matchedId}/observe`,
                        allowedErrorCodes: [404],
                    }),
                    await get({
                        url: `/multiaccess/memberbooth/label/${matchedId}/membership`,
                        allowedErrorCodes: [404],
                    }),
                ]);
                label = observeRes.data as LabelActionResponse | null;
                membership = membershipRes.data as membership_t;
            } else {
                // Try old format
                const data = JSON.parse(scannedString);
                if (
                    data["v"] >= 1 &&
                    data["v"] <= 2 &&
                    data.hasOwnProperty("member_number")
                ) {
                    // Seems legit. Try to observe the label by id, which is just the timestamp for v1 and v2 labels
                    const observeRes = await post({
                        url: `/multiaccess/memberbooth/label/${data.unix_timestamp}/observe`,
                        allowedErrorCodes: [404],
                    });

                    if (observeRes.data == null) {
                        // Submit unknown label and migrate to new format in the process
                        const createRes = await post({
                            url: "/multiaccess/memberbooth/label",
                            data: data,
                        });
                        const createdLabel = createRes.data as UploadedLabel;
                        console.log(createdLabel);

                        // Observe the new label
                        const [observeRes2, membershipRes] = await Promise.all([
                            post({
                                url: `/multiaccess/memberbooth/label/${createdLabel.label.id}/observe`,
                                allowedErrorCodes: [404],
                            }),
                            await get({
                                url: `/multiaccess/memberbooth/label/${createdLabel.label.id}/membership`,
                            }),
                        ]);
                        label = observeRes2.data as LabelActionResponse | null;
                        membership = membershipRes.data as membership_t;
                    } else {
                        const membershipRes = await get({
                            url: `/multiaccess/memberbooth/label/${data.unix_timestamp}/membership`,
                        });
                        label = observeRes.data as LabelActionResponse;
                        membership = membershipRes.data as membership_t;
                    }
                }
            }
        } catch (err) {
            // If it's a network error, just return. Don't store in cache.
            if (err && (err as any).name === "NetworkError") {
                return null;
            }
            console.error(err);
            label = null;
        }

        if (label === null || membership == null) {
            // Store null in cache to avoid repeated lookups
            scanCache.current.set(scannedString, null);
            return null;
        }

        // Store in cache
        const cache_item = { label, membership };
        scanCache.current.set(scannedString, cache_item);
        return cache_item;
    };

    const fadeoutLabelItem = (item: {
        label: LabelActionResponse;
        membership: membership_t;
        state: "active" | "fading-out";
        timer: NodeJS.Timeout;
    }) => {
        if (item.state === "fading-out") return;
        item.state = "fading-out";
        window.clearTimeout(item.timer);
        item.timer = setTimeout(() => {
            setLastScanResult((current) => current.filter((i) => i !== item));
        }, 1000);
    };

    const fadeoutLabel = (id: number) => {
        setLastScanResult((prev) => {
            const item = prev.find((v) => v.label.id === id);
            if (item) {
                fadeoutLabelItem(item);
            }
            return [...prev];
        });
    };

    // Handles the scan event, queues if busy
    const scanCallback = (scannedString: string) => {
        if (isScanning.current) {
            setPendingScan(scannedString);
            return;
        }
        isScanning.current = true;
        processScan(scannedString)
            .then((label) => {
                // Timer logic for null label
                if (!label) return;

                console.log("Finished scan", label);
                setLastScanResult((prev) => {
                    // Remove any existing entry for this label
                    for (const v of prev) {
                        if (v.label.id === label.label.id) {
                            window.clearTimeout(v.timer);
                        }
                    }
                    prev = prev.filter((v) => v.label.id !== label.label.id);

                    // Mark any existing entries for removal
                    for (const v of prev) {
                        fadeoutLabelItem(v);
                    }
                    return [
                        ...prev,
                        {
                            ...label,
                            state: "active",
                            timer: setTimeout(
                                () => fadeoutLabel(label.label.id),
                                3000,
                            ),
                        },
                    ];
                });
            })
            .finally(() => {
                isScanning.current = false;
            });
    };

    const handleLabelIdSelect = useCallback(
        async (labelId: number) => {
            setShowLabelIdSearch(false);
            // Simulate a scan by fetching and displaying the label
            const [observeRes, membershipRes] = await Promise.all([
                post({
                    url: `/multiaccess/memberbooth/label/${labelId}/observe`,
                    allowedErrorCodes: [404],
                }),
                get({
                    url: `/multiaccess/memberbooth/label/${labelId}/membership`,
                    allowedErrorCodes: [404],
                }),
            ]);
            if (observeRes.data && membershipRes.data) {
                setLastScanResult([
                    {
                        label: observeRes.data,
                        membership: membershipRes.data,
                        state: "active",
                        timer: setTimeout(
                            () => fadeoutLabel(observeRes.data.id),
                            3000,
                        ),
                    },
                ]);
            }
        },
        [setLastScanResult],
    );

    // Effect to process pending scans
    useEffect(() => {
        if (!isScanning && pendingScan) {
            setPendingScan(null);
            scanCallback(pendingScan);
        }
    }, [isScanning, pendingScan]);

    return (
        <div className="box-terminator">
            <div style={{ position: "relative" }}>
                <button
                    className="label-id-search-btn"
                    style={{
                        position: "absolute",
                        top: 10,
                        right: 10,
                        zIndex: 10,
                        fontSize: "2em",
                        background: "#fff",
                        border: "1px solid #ccc",
                        borderRadius: "50%",
                        width: "48px",
                        height: "48px",
                    }}
                    title="Search by label ID"
                    onClick={() => setShowLabelIdSearch(true)}
                >
                    #
                </button>
                {showLabelIdSearch && (
                    <LabelIdSearchPopover
                        onSelect={handleLabelIdSelect}
                        onClose={() => setShowLabelIdSearch(false)}
                    />
                )}
                <QrCodeScanner onSuccess={scanCallback} />
            </div>
            {lastScanResult.map((item) => {
                return (
                    <ScanResultPopover
                        key={item.label.id}
                        labelAction={item.label}
                        membership={item.membership}
                        state={item.state}
                    />
                );
            })}
        </div>
    );
};

export default BoxTerminator;
