import Icon from "Components/icons";
import {
    labelExpiryDate,
    labelFirstValidTerminationDate,
    labelIsExpired,
    LabelMaxRelativeDays,
    LabelMessageTemplate,
    LabelMessageTemplates,
    membership_t,
    Message,
    MessageTemplate,
    UploadedLabel,
} from "frontend_common";
import { get, post } from "gateway";
import { Translator, useTranslation } from "i18n/hooks";
import i18next from "i18next";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActiveLogo } from "./ActiveLogo";
import { ExpiredLogo } from "./ExpiredLogo";
import QrCodeScanner from "./QrCodeScanner";

export interface LabelActionResponse {
    id: number;
    label: UploadedLabel;
    messages_to_send: MessageTemplate[];
}

const labelUrlRegex = /\/L\/([0-9_-]+)$/;

export const dateToRelative = (
    now: Date,
    date: Date,
    t: Translator<"time">,
    mode: "relative_generic",
) => {
    const diffMs = date.getTime() - now.getTime();
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);

    // Show relative if within ±LabelMaxRelativeDays days
    if (Math.abs(diffDay) < LabelMaxRelativeDays) {
        if (diffDay === 0) {
            if (Math.abs(diffHour) < 24) {
                if (diffHour === 0) {
                    if (Math.abs(diffMin) < 60) {
                        if (diffMin === 0) {
                            return t(`${mode}.now`);
                        }
                        return t(
                            diffMin > 0
                                ? `${mode}.in_minutes`
                                : `${mode}.minutes_ago`,
                            { count: Math.abs(diffMin) },
                        );
                    }
                    return t(
                        diffHour > 0 ? `${mode}.in_hours` : `${mode}.hours_ago`,
                        { count: Math.abs(diffHour) },
                    );
                }
                return t(
                    diffHour > 0 ? `${mode}.in_hours` : `${mode}.hours_ago`,
                    { count: Math.abs(diffHour) },
                );
            }
            return t(diffDay > 0 ? `${mode}.in_days` : `${mode}.days_ago`, {
                count: Math.abs(diffDay),
            });
        }
        return t(diffDay > 0 ? `${mode}.in_days` : `${mode}.days_ago`, {
            count: Math.abs(diffDay),
        });
    }

    // Otherwise, show absolute
    const fourMonthsMs = 4 * 30 * 24 * 60 * 60 * 1000;
    let options: Intl.DateTimeFormatOptions = {
        month: "short",
        day: "numeric",
        hour: undefined,
        minute: undefined,
    };
    if (Math.abs(date.getTime() - now.getTime()) > fourMonthsMs) {
        // Several months difference, include year
        options.year = "numeric";
    }
    const date_str = date.toLocaleString(i18next.language, options);
    return date.getTime() < now.getTime()
        ? t(`${mode}.date_past`, { date: date_str })
        : t(`${mode}.date_future`, { date: date_str });
};

const ScanResultPopover = ({
    labelAction,
    membership,
    state,
    messages,
}: {
    labelAction: LabelActionResponse;
    membership: membership_t;
    state: "active" | "fading-out";
    messages: Message[];
}) => {
    const label = labelAction.label.label;
    const now = new Date();
    const expiresAt = labelExpiryDate(label, membership);
    const isExpired = labelIsExpired(now, label, membership);
    const terminationDate = labelFirstValidTerminationDate(expiresAt, messages);
    const { t: t_time } = useTranslation("time");
    const { t } = useTranslation("box_terminator");

    for (const m of labelAction.messages_to_send) {
        if (!LabelMessageTemplates.includes(m as LabelMessageTemplate)) {
            console.warn("Unknown message template", m);
        }
    }
    const messagesToSend =
        labelAction.messages_to_send as LabelMessageTemplate[];

    return (
        <>
            <div
                className={
                    `box-terminator-popover` +
                    (state === "fading-out" ? " fading-out" : "") +
                    (isExpired ? " expired" : " active")
                }
            >
                <div>
                    <div>{isExpired ? <ExpiredLogo /> : <ActiveLogo />}</div>
                    {terminationDate != null && (
                        <div>
                            {terminationDate <= now
                                ? t("can_terminate")
                                : t("can_be_terminated_in", {
                                      relative_time: dateToRelative(
                                          now,
                                          terminationDate,
                                          t_time,
                                          "relative_generic",
                                      ),
                                  })}
                        </div>
                    )}
                    {expiresAt && terminationDate == null && (
                        <div className="uk-flex-1">
                            {t(
                                expiresAt.getTime() > now.getTime()
                                    ? "expires_future"
                                    : "expires_past",
                                {
                                    relative_time: dateToRelative(
                                        now,
                                        expiresAt,
                                        t_time,
                                        "relative_generic",
                                    ),
                                },
                            )}
                        </div>
                    )}
                    <a
                        href={labelAction.label.public_url}
                        className="uk-button uk-button-default"
                    >
                        {t("view_label")}
                    </a>
                </div>
            </div>
            {messagesToSend.length > 0 && (
                <div
                    className={
                        `messages-to-send-popover` +
                        (state === "fading-out" ? " fading-out" : "")
                    }
                >
                    <ul>
                        {messagesToSend.map((msg, idx) => (
                            <li key={idx} className="messages-to-send-item">
                                <Icon
                                    icon={
                                        msg.includes("sms") ? "comment" : "mail"
                                    }
                                />
                                <span>
                                    {t("will_send")}{" "}
                                    <strong>
                                        {t(`message_templates.${msg}`)}
                                    </strong>
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </>
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
    const [results, setResults] = useState<UploadedLabel[]>([]);
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

    const { t } = useTranslation("box_terminator");

    return (
        <div className="label-id-search-popover">
            {loading && results.length == 0 && <div>Searching…</div>}
            <ul>
                {results.map((label) => (
                    <li key={label.label.id}>
                        <button
                            className="label-search-result"
                            onClick={() => onSelect(label.label.id)}
                        >
                            {label.label.id} –{" "}
                            {label.label.type === "TemporaryStorageLabel"
                                ? label.label.description
                                : label.label.type}
                        </button>
                    </li>
                ))}
            </ul>
            {results.length === 0 && input.length > 0 && !loading && (
                <div>{t("no_matching_labels")}</div>
            )}
            <input
                className="label-id-input"
                type="tel"
                pattern="[0-9]*"
                inputMode="numeric"
                autoFocus
                placeholder={t("enter_label_id")}
                value={input}
                onChange={(e) => setInput(e.target.value.replace(/\D/g, ""))}
                // Close after a short time, to allow other click events to register
                onBlur={() => setTimeout(onClose, 100)}
            />
        </div>
    );
};

type ScanItem = {
    label: LabelActionResponse;
    membership: membership_t;
    messages: Message[];
    state: "active" | "fading-out";
    timer: NodeJS.Timeout;
};

type ScanResult = {
    label: LabelActionResponse;
    membership: membership_t;
    messages: Message[];
};

const BoxTerminator = () => {
    // Ensure only a single request is in flight at any one time
    const isScanning = useRef(false);
    const [pendingScan, setPendingScan] = useState<string | null>(null);
    const [lastScanResult, setLastScanResult] = useState<ScanItem[]>([]);
    const scanCache = useRef(new Map<string, ScanResult | null>());
    const [showLabelIdSearch, setShowLabelIdSearch] = useState(false);

    const processScan = async (
        scannedString: string,
    ): Promise<ScanResult | null> => {
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
        let messages: Message[] = [];
        try {
            if (matchedId !== null) {
                const [observeRes, membershipRes, messageRes] =
                    await Promise.all([
                        post({
                            url: `/multiaccess/memberbooth/label/${matchedId}/observe`,
                            allowedErrorCodes: [404],
                        }),
                        await get({
                            url: `/multiaccess/memberbooth/label/${matchedId}/membership`,
                            allowedErrorCodes: [404],
                        }),
                        await get({
                            url: `/multiaccess/memberbooth/label/${matchedId}/message`,
                            allowedErrorCodes: [404],
                        }),
                    ]);
                label = observeRes.data as LabelActionResponse | null;
                membership = membershipRes.data as membership_t;
                messages = (messageRes.data ?? []) as Message[];
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
                        const [observeRes2, membershipRes, messageRes] =
                            await Promise.all([
                                post({
                                    url: `/multiaccess/memberbooth/label/${createdLabel.label.id}/observe`,
                                    allowedErrorCodes: [404],
                                }),
                                await get({
                                    url: `/multiaccess/memberbooth/label/${createdLabel.label.id}/membership`,
                                }),
                                await get({
                                    url: `/multiaccess/memberbooth/label/${createdLabel.label.id}/message`,
                                }),
                            ]);
                        label = observeRes2.data as LabelActionResponse | null;
                        membership = membershipRes.data as membership_t;
                        messages = (messageRes.data ?? []) as Message[];
                    } else {
                        const [membershipRes, messageRes] = await Promise.all([
                            get({
                                url: `/multiaccess/memberbooth/label/${data.unix_timestamp}/membership`,
                            }),
                            get({
                                url: `/multiaccess/memberbooth/label/${data.unix_timestamp}/message`,
                            }),
                        ]);
                        label = observeRes.data as LabelActionResponse;
                        membership = membershipRes.data as membership_t;
                        messages = (messageRes.data ?? []) as Message[];
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
        const cache_item = { label, membership, messages };
        scanCache.current.set(scannedString, cache_item);
        return cache_item;
    };

    const fadeoutLabelItem = (item: ScanItem) => {
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
            const [observeRes, membershipRes, messageRes] = await Promise.all([
                post({
                    url: `/multiaccess/memberbooth/label/${labelId}/observe`,
                    allowedErrorCodes: [404],
                }),
                get({
                    url: `/multiaccess/memberbooth/label/${labelId}/membership`,
                    allowedErrorCodes: [404],
                }),
                get({
                    url: `/multiaccess/memberbooth/label/${labelId}/message`,
                    allowedErrorCodes: [404],
                }),
            ]);
            if (observeRes.data && membershipRes.data && messageRes.data) {
                setLastScanResult([
                    {
                        label: observeRes.data,
                        membership: membershipRes.data,
                        messages: messageRes.data ?? [],
                        state: "active",
                        timer: setTimeout(
                            () => fadeoutLabel(observeRes.data.id),
                            10000, // Use a longer timeout for manual selection
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
            {!showLabelIdSearch && (
                <button
                    className="label-id-search-btn"
                    title="Search by label ID"
                    onClick={() => setShowLabelIdSearch(true)}
                >
                    #
                </button>
            )}
            {showLabelIdSearch && (
                <LabelIdSearchPopover
                    onSelect={handleLabelIdSelect}
                    onClose={() => setShowLabelIdSearch(false)}
                />
            )}
            <QrCodeScanner onSuccess={scanCallback} />
            {lastScanResult.map((item) => {
                return (
                    <ScanResultPopover
                        key={item.label.id}
                        labelAction={item.label}
                        membership={item.membership}
                        messages={item.messages}
                        state={item.state}
                    />
                );
            })}
        </div>
    );
};

export default BoxTerminator;
