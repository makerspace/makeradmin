import {
    DryingLabel,
    FireSafetyLabel,
    labelExpiresSoon,
    labelExpiryDate,
    labelFirstValidTerminationDate,
    labelIsExpired,
    LabelMessageTemplate,
    LabelMessageTemplates,
    membership_t,
    Permission,
    TemporaryStorageLabel,
    UploadedLabel,
} from "frontend_common";
import { Message } from "frontend_common/src/message";
import { render } from "preact";
import { render as jsx_to_string } from "preact-render-to-string";
import { useEffect, useRef, useState } from "preact/hooks";
import * as common from "./common";
import { NOT_FOUND, UNAUTHORIZED } from "./common";
import { useTranslation } from "./i18n";
import { dateToRelative } from "./label_common";
import * as login from "./login";
import { LoadCurrentPermissions } from "./member_common";
import { NotFoundPage } from "./notfound";

declare var UIkit: any;

const fitTextToWidth = (
    maxWidthPx: number,
    wrapCharsPerLine: number | undefined,
    el: HTMLElement | null,
) => {
    if (!el) return;

    let min = 10;
    let max = 200;
    let best = min;

    // Temporarily set white-space to nowrap for accurate measurement
    const originalWhiteSpace = el.style.whiteSpace;
    el.style.whiteSpace = "nowrap";

    const originalText = el.textContent ?? "";
    let wrapped =
        wrapCharsPerLine !== undefined &&
        originalText.length > wrapCharsPerLine;
    if (wrapped) {
        el.textContent = originalText.substring(0, wrapCharsPerLine); // Limit to N chars per line
    }

    while (min <= max) {
        const mid = Math.floor((min + max) / 2);
        el.style.fontSize = `${mid}px`;
        const width = el.scrollWidth;

        if (width <= maxWidthPx) {
            best = mid;
            min = mid + 1;
        } else {
            max = mid - 1;
        }
    }

    el.style.fontSize = `calc(${best * 0.98}px * var(--scale))`;
    el.style.whiteSpace = originalWhiteSpace;

    if (wrapped) {
        el.textContent = originalText;
    }
};

const maxWidthPx = 500 - 40 * 2; // Label width minus padding
const contentPadding = 10; // Padding of the #content div
const maxFractionOfViewport = 0.6;

export const FitLabel = ({
    children,
    className,
    maxCharsPerRow,
}: React.PropsWithChildren<{
    className?: string;
    maxCharsPerRow?: number;
}>) => {
    const textRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        fitTextToWidth(maxWidthPx, maxCharsPerRow, textRef.current);

        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => {
                console.log(
                    "Fitting text when fonts ready:",
                    children,
                    textRef.current,
                );
                fitTextToWidth(maxWidthPx, maxCharsPerRow, textRef.current);
            });
        }
    }, [children, maxCharsPerRow]);

    return (
        <div
            className={
                (className ?? "") +
                " fit-label " +
                (maxCharsPerRow !== undefined ? "fit-label-wrap" : "")
            }
            ref={textRef}
        >
            {children}
        </div>
    );
};

export const LabelTemporaryStorageComponent = ({
    label,
    membership,
}: {
    label: TemporaryStorageLabel;
    membership: membership_t | null;
}) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleResize = () => {
            const el = containerRef.current;
            if (!el) return;
            const vw =
                (Math.max(
                    document.documentElement.clientWidth || 0,
                    window.innerWidth || 0,
                ) -
                    contentPadding * 2) *
                maxFractionOfViewport;
            const scale = Math.min(1, vw / 500);
            el.style.setProperty("--scale", scale.toString());
        };
        handleResize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    return (
        <div
            className={`label-print-tempstorage ${
                labelExpiresSoon(new Date(), label, membership)
                    ? "label-expiring-soon"
                    : ""
            } ${
                labelIsExpired(new Date(), label, membership)
                    ? "label-expired"
                    : "label-active"
            }`}
            ref={containerRef}
        >
            <FitLabel>TEMPORARY STORAGE</FitLabel>
            <div className="label-print-qr"></div>
            <FitLabel>
                #{label.member_number}
                <br />
                {label.member_name}
            </FitLabel>
            <FitLabel>
                THE BOARD CAN THROW THIS AWAY AFTER
                <br />
                <span className="label-expires-at">{label.expires_at}</span>
            </FitLabel>
            <FitLabel maxCharsPerRow={40}>{label.description}</FitLabel>
        </div>
    );
};

export const FireSafetyLabelComponent = ({
    label,
}: {
    label: FireSafetyLabel;
}) => {
    return (
        <div className="label-print-tempstorage">
            <FitLabel>STORE IN FIRE SAFETY CABINET</FitLabel>
            <FitLabel>THIS PRODUCT BELONGS TO</FitLabel>
            <FitLabel>#{label.member_number}</FitLabel>
            <FitLabel>{label.member_name}</FitLabel>
            <FitLabel>ANY MEMBER CAN USE THIS PRODUCT FROM</FitLabel>
            <FitLabel className="label-expires-at">{label.expires_at}</FitLabel>
        </div>
    );
};

export const DryingLabelComponent = ({ label }: { label: DryingLabel }) => {
    return (
        <div className="label-print-tempstorage">
            <FitLabel>DONE DRYING BY</FitLabel>
            <FitLabel className="label-expires-at">
                {new Date(label.expires_at).toLocaleString("sv-SE", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                })}
            </FitLabel>
            <FitLabel>#{label.member_number}</FitLabel>
            <FitLabel>{label.member_name}</FitLabel>
        </div>
    );
};

type ActionType = "report" | "terminate";

const isMobileWithCamera = () => {
    if (
        "userAgentData" in navigator &&
        (navigator.userAgentData as any).mobile !== undefined
    ) {
        return (navigator.userAgentData as any).mobile;
    }

    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
        navigator.userAgent,
    );
};

const TerminationButton = ({
    expiresAt,
    firstCleanoutTime,
    onClick,
}: {
    expiresAt: Date | null;
    firstCleanoutTime: Date | null;
    onClick: () => void;
}) => {
    const { t } = useTranslation("labels");

    if (!expiresAt) {
        return null;
    }

    const now = new Date();

    if (firstCleanoutTime) {
        if (firstCleanoutTime < now) {
            return (
                <button
                    className="uk-button uk-button-danger uk-margin-left"
                    onClick={onClick}
                >
                    {t("actions.terminate")}
                </button>
            );
        } else {
            return (
                <button
                    className="uk-button uk-button-danger uk-margin-left"
                    disabled
                >
                    {t("actions.can_terminate_in", {
                        duration: dateToRelative(
                            now,
                            firstCleanoutTime,
                            t,
                            "relative_generic",
                        ).toLowerCase(),
                    })}
                </button>
            );
        }
    } else {
        return (
            <button
                className="uk-button uk-button-danger uk-margin-left"
                disabled
            >
                {t("actions.can_terminate_after_observation")}
            </button>
        );
    }
};

const LabelActions = ({
    label,
    onSentMessage,
    messages,
    membership,
}: {
    label: UploadedLabel;
    onSentMessage: () => void;
    messages: Message[];
    membership: membership_t;
}) => {
    const { t } = useTranslation("labels");
    const [modalOpen, setModalOpen] = useState<null | ActionType>(null);
    const [message, setMessage] = useState("");
    const [image, setImage] = useState<File | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Camera prompt
    const inputRef = useRef<HTMLInputElement>(null);
    const modalRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Prevent cleaning out an item, unless an expiration warning has been sent at least N days ago
    const now = new Date();
    const expiresAt = labelExpiryDate(label.label, membership);
    let firstCleanoutTime: Date | null = labelFirstValidTerminationDate(
        expiresAt,
        messages,
    );

    useEffect(() => {
        if (modalOpen && inputRef.current && textareaRef.current) {
            if (isMobileWithCamera()) {
                inputRef.current.click();
            } else {
                setTimeout(() => {
                    textareaRef.current?.focus();
                    textareaRef.current?.setSelectionRange(
                        textareaRef.current.value.length,
                        textareaRef.current.value.length,
                    );
                }, 10); // Delay to allow modal to finish opening. Not quite sure why this is required, but it is.
            }
        }
    }, [modalOpen]);

    useEffect(() => {
        if (modalRef.current) {
            if (modalOpen) {
                UIkit.modal(modalRef.current).show();
            } else {
                UIkit.modal(modalRef.current).hide();
            }
        }
    }, [modalOpen]);

    useEffect(() => {
        UIkit.util.on(modalRef.current, "hidden", () => {
            setModalOpen(null);
        });
    }, [modalRef]);

    const handleFileChange = (e: Event) => {
        const files = (e.target as HTMLInputElement).files;
        if (files && files.length > 0) {
            setImage(files[0]!);
            // Note: This doesn't seem to work on mobile. Probably because they require an actual click event to allow it.
            textareaRef.current?.focus();
            textareaRef.current?.setSelectionRange(
                textareaRef.current.value.length,
                textareaRef.current.value.length,
            );
        }
    };

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const formData = new FormData();
            formData.append("message", message);
            if (image) formData.append("image", image);

            const endpoint =
                modalOpen === "report"
                    ? `${apiBasePath}/multiaccess/memberbooth/label/${label.label.id}/report`
                    : `${apiBasePath}/multiaccess/memberbooth/label/${label.label.id}/terminate`;

            await common.ajax("POST", endpoint, formData);
            onSentMessage();

            UIkit.notification({
                message: t("actions.submitted_successfully"),
                status: "success",
            });
            setModalOpen(null);
            setMessage("");
            setImage(null);
        } catch (err) {
            UIkit.notification({
                message: t("actions.failed_to_submit"),
                status: "danger",
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <>
            <div className="label-actions uk-flex uk-flex-row">
                <button
                    className="uk-button uk-button-default"
                    onClick={() => setModalOpen("report")}
                >
                    {t("actions.report")}
                </button>
                {expiresAt && now.getTime() > expiresAt.getTime() && (
                    <TerminationButton
                        expiresAt={expiresAt}
                        firstCleanoutTime={firstCleanoutTime}
                        onClick={() => setModalOpen("terminate")}
                    />
                )}
            </div>
            <div uk-modal className="uk-modal" ref={modalRef}>
                <div className="uk-modal-dialog uk-modal-body">
                    <h2 className="uk-modal-title">
                        {modalOpen === "report"
                            ? t("actions.report_label")
                            : t("actions.terminate_label")}
                    </h2>
                    <form onSubmit={handleSubmit}>
                        <div className="uk-margin">
                            <textarea
                                className="uk-textarea"
                                rows={3}
                                placeholder={t("actions.write_a_message")}
                                value={message}
                                onInput={(e) =>
                                    setMessage(
                                        (e.target as HTMLTextAreaElement).value,
                                    )
                                }
                                ref={textareaRef}
                                required
                            />
                        </div>
                        <div className="uk-margin">
                            <input
                                type="file"
                                accept="image/*"
                                capture={"environment"}
                                style={{ display: "none" }}
                                ref={inputRef}
                                onChange={handleFileChange}
                            />
                            <button
                                type="button"
                                className="uk-button uk-button-default"
                                onClick={() => inputRef.current?.click()}
                            >
                                {image
                                    ? t("actions.change_photo")
                                    : t("actions.add_photo")}
                            </button>
                            {image && (
                                <span style={{ marginLeft: 8 }}>
                                    {image.name}
                                </span>
                            )}
                        </div>
                        <div className="uk-margin">
                            <button
                                type="submit"
                                className="uk-button uk-button-primary"
                                disabled={submitting}
                            >
                                {t("actions.submit")}
                            </button>
                            <button
                                type="button"
                                className="uk-button uk-button-default"
                                onClick={() => setModalOpen(null)}
                                style={{ marginLeft: 8 }}
                            >
                                {t("actions.cancel")}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    );
};

const LabelMessage = ({
    message,
    showMessageLink,
}: {
    message: Message;
    showMessageLink: boolean;
}) => {
    const { t } = useTranslation("labels");

    const template = message.template as LabelMessageTemplate;

    if (template === null || !LabelMessageTemplates.includes(template)) {
        return <li>Unexpected message template: {template}</li>;
    }

    return (
        <li>
            <a
                href={
                    showMessageLink
                        ? `${window.hostAdminFrontend}/messages/${message.id}`
                        : undefined
                }
            >
                <span className="label-message-date">
                    {dateToRelative(
                        new Date(),
                        new Date(message.created_at),
                        t,
                        "relative_generic",
                    )}
                </span>
                <span>{t(`messages.template.${template}`)}</span>
                <span className={"uk-flex-1"}></span>
                {message.status != "sent" && (
                    <span className="label-message-status">
                        {t(`messages.status.${message.status}`)}
                    </span>
                )}
            </a>
        </li>
    );
};

const LabelPage = ({
    membership: membership,
    label,
    showActions,
    messages: initial_messages,
    showMessageLinks,
}: {
    membership: membership_t | null;
    label: UploadedLabel;
    showActions: boolean;
    messages: Message[];
    showMessageLinks: boolean;
}) => {
    const { t } = useTranslation("labels");

    // Split labels into active and expired
    const now = new Date();

    let comp: React.ReactElement | null = null;
    if (label.label.type === "TemporaryStorageLabel") {
        comp = (
            <LabelTemporaryStorageComponent
                label={label.label}
                membership={membership}
            />
        );
    } else if (label.label.type === "FireSafetyLabel") {
        comp = <FireSafetyLabelComponent label={label.label} />;
    } else if (label.label.type === "DryingLabel") {
        comp = <DryingLabelComponent label={label.label} />;
    }

    const [messages, setMessages] = useState(initial_messages);

    const [lastActionTime, setLastActionTime] = useState<Date | null>(null);

    useEffect(() => {
        let timeoutId: number | undefined;

        const fetchMessages = () => {
            LoadLabelMessages(label.label.id)
                .then(setMessages)
                .finally(() => {
                    let intervalMs = 30000;
                    if (lastActionTime) {
                        const now = Date.now();
                        const diff = now - lastActionTime.getTime();
                        // If action was within last 1 minute, poll often, otherwise more slowly
                        intervalMs = diff < 60 * 1000 ? 2000 : 60000;
                    }
                    timeoutId = window.setTimeout(fetchMessages, intervalMs);
                });
        };

        fetchMessages();

        return () => {
            if (timeoutId !== undefined) {
                clearTimeout(timeoutId);
            }
        };
    }, [label.label.id, lastActionTime]);

    // Pass setLastActionTime to LabelActions so it can update when an action is performed

    return (
        <>
            {comp ? (
                comp
            ) : (
                <div>
                    Label type {label.label.type} not supported for display yet.
                </div>
            )}
            {showActions && (
                <>
                    <h3>{t("actions.title")}</h3>
                    <LabelActions
                        label={label}
                        onSentMessage={() => setLastActionTime(new Date())}
                        messages={messages}
                        membership={membership!}
                    />
                </>
            )}
            {messages.length > 0 && (
                <>
                    <h3>{t("messages.title")}</h3>
                    <ul className="uk-list label-messages">
                        {messages.map((msg) => (
                            <LabelMessage
                                key={msg.id}
                                message={msg}
                                showMessageLink={showMessageLinks}
                            />
                        ))}
                    </ul>
                </>
            )}
        </>
    );
};

const LoadLabelMessages = (labelId: number) => {
    return common
        .ajax(
            "GET",
            `${window.apiBasePath}/multiaccess/memberbooth/label/${labelId}/message`,
        )
        .then((r) => r.data as Message[])
        .catch((e) => (e.status == UNAUTHORIZED ? [] : Promise.reject(e)));
};

const apiBasePath = window.apiBasePath;
function getLabelIdFromPath(): number | null {
    const match = window.location.pathname.match(/\/label\/(\d+)/);
    return match ? parseInt(match[1]!, 10) : null;
}

const labelId = getLabelIdFromPath();
const future2 = common
    .ajax(
        "GET",
        `${window.apiBasePath}/multiaccess/memberbooth/label/${labelId}/membership`,
    )
    .then((r) => r.data as membership_t)
    .catch((e) => (e.status == UNAUTHORIZED ? null : Promise.reject(e)));

const future3 = common
    .ajax(
        "GET",
        `${window.apiBasePath}/multiaccess/memberbooth/label/${labelId}`,
    )
    .then((r) => r.data as UploadedLabel);
const future4 = LoadCurrentPermissions();
const future5 = labelId
    ? LoadLabelMessages(labelId)
    : Promise.resolve([] as Message[]);

common.documentLoaded().then(() => {
    const root = document.querySelector("#label-page") as HTMLElement;

    Promise.all([future2, future3, future4, future5] as const)
        .then(([membership, label, permissions, messages]) => {
            root.innerHTML = "";
            const showActionsPermission: Permission = "message_send";
            const showMessageLinksPermission: Permission = "message_view";
            const showMessageLinks = permissions.includes(
                showMessageLinksPermission,
            );
            render(
                <LabelPage
                    membership={membership}
                    label={label}
                    showActions={permissions.includes(showActionsPermission)}
                    messages={messages}
                    showMessageLinks={showMessageLinks}
                />,
                root,
            );
        })
        .catch((e) => {
            // Probably Unauthorized, redirect to login page.
            console.error(e);
            if (e.status === NOT_FOUND) {
                render(<NotFoundPage />, root);
            } else if (e.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert(
                    jsx_to_string(
                        <>
                            <h2>Failed to load data</h2>
                            <pre>{JSON.stringify(e)}</pre>
                        </>,
                    ),
                );
            }
        });
});
