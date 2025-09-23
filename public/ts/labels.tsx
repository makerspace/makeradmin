import { member_t, membership_t, UploadedLabel } from "frontend_common";
import { render } from "preact";
import { render as jsx_to_string } from "preact-render-to-string";
import { useEffect, useMemo, useState } from "preact/hooks";
import * as common from "./common";
import { UNAUTHORIZED } from "./common";
import { useTranslation } from "./i18n";
import {
    dateToRelative,
    DeleteButton,
    expiredRecently,
    expiresSoon,
    isExpired,
} from "./label_common";
import * as login from "./login";
import {
    LoadCurrentLabels,
    LoadCurrentMemberInfo,
    LoadCurrentMembershipInfo,
} from "./member_common";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const LabelsList = ({
    labels,
    onChangeLabels,
    filter,
    now,
    membership,
}: {
    labels: UploadedLabel[];
    now: Date;
    filter: (label: UploadedLabel) => boolean;
    onChangeLabels: (labels: UploadedLabel[]) => void;
    membership: membership_t;
}) => {
    const { t } = useTranslation("labels");
    if (labels.length === 0) {
        return <p>{t("no_labels_uploaded")}</p>;
    }

    // Precompute expired status for all labels
    const filtered = useMemo(() => {
        const initialFilter = labels.filter((label) => {
            if (!filter(label)) return false;
            if (
                label.label.type === "TemporaryStorageLabel" ||
                label.label.type === "FireSafetyLabel"
            ) {
                return true;
            }
            if (label.label.type === "DryingLabel") {
                const created = new Date(label.label.created_at);
                const diff = now.getTime() - created.getTime();
                return diff <= 14 * 24 * 60 * 60 * 1000;
            }
            return false;
        });

        const deduped: (UploadedLabel & { variants: UploadedLabel[] })[] = [];
        for (let i = 0; i < initialFilter.length; ++i) {
            const curr = initialFilter[i]!;
            const prev = deduped[deduped.length - 1];
            if (
                prev &&
                curr.label.type === prev.label.type &&
                curr.label.member_number === prev.label.member_number &&
                ("description" in curr.label && "description" in prev.label
                    ? curr.label.description === prev.label.description
                    : true) &&
                "expires_at" in curr.label &&
                "expires_at" in prev.label &&
                Math.abs(
                    new Date(curr.label.expires_at).getTime() -
                        new Date(prev.label.expires_at).getTime(),
                ) <
                    5 * 60 * 1000 // 5 minutes
            ) {
                prev.variants.push(curr);
                continue;
            }
            deduped.push({
                ...curr,
                variants: [curr],
            });
        }
        return deduped;
    }, [labels, filter, now]);

    // Determine which are expired
    const expiredInfo = filtered.map(({ label }) => {
        let expiresAt: string | null = null;
        if (
            label.type === "TemporaryStorageLabel" ||
            label.type === "DryingLabel"
        ) {
            expiresAt = label.expires_at;
        }
        return isExpired(now, label, membership);
    });

    // Find the index of the first expired label
    const firstExpiredIdx = expiredInfo.findIndex((x) => x);

    return (
        <ul className="uk-list">
            {filtered.map(({ public_url, label }, idx) => {
                let expiresAt: string | null = null;
                if (
                    label.type === "TemporaryStorageLabel" ||
                    label.type === "DryingLabel" ||
                    label.type === "FireSafetyLabel"
                ) {
                    expiresAt = label.expires_at;
                }
                const expiringSoon = expiresSoon(now, label, membership);
                const didExpireRecently = expiredRecently(
                    now,
                    label,
                    membership,
                );

                // Expired logic
                const isExpired = expiredInfo[idx];
                let opacity = 1;
                let fadeClass = "";
                if (isExpired) {
                    const fadeIdx = idx - firstExpiredIdx;
                    opacity = Math.max(0.2, 1 - fadeIdx / 5);
                    fadeClass = "label-expired";
                } else {
                    fadeClass = "label-active";
                }

                // Choose icon
                let icon = "tag";
                if (label.type === "TemporaryStorageLabel") icon = "clock";
                else if (label.type === "Printer3DLabel") icon = "nut";
                else if (label.type === "FireSafetyLabel")
                    icon = "paint-bucket";

                return (
                    <li
                        key={label.id}
                        className={`uk-flex uk-flex-between ${fadeClass} ${
                            expiringSoon ? "label-expiring-soon" : ""
                        } ${didExpireRecently ? "label-expired-recently" : ""}`}
                        style={{ opacity }}
                    >
                        <a href={public_url}>
                            <span
                                className="uk-margin-small-right uk-flex-none"
                                uk-icon={`icon: ${icon}`}
                            ></span>
                            <span className="label-type">
                                {t(`label_type.${label.type}`)}
                            </span>
                            {label.type === "TemporaryStorageLabel" &&
                            label.description ? (
                                <strong className="label-description">
                                    : {label.description}
                                </strong>
                            ) : (
                                ""
                            )}
                            <div className="uk-flex-1"></div>
                            {expiresAt && (
                                <>
                                    <span className="uk-flex-none">
                                        {dateToRelative(
                                            now,
                                            new Date(expiresAt),
                                            t,
                                            label.type === "DryingLabel"
                                                ? "drying"
                                                : "expiry",
                                        )}
                                    </span>
                                </>
                            )}
                            <DeleteButton
                                labelId={label.id}
                                onDelete={async (labelId) => {
                                    // Find the label in the filtered list to get its variants
                                    const filteredItem = filtered.find(
                                        (f) => f.label.id === labelId,
                                    );
                                    if (!filteredItem) return;
                                    let idsToRemove = filteredItem.variants.map(
                                        (v) => v.label.id,
                                    );
                                    const newLabels = labels.filter(
                                        (l) =>
                                            !idsToRemove.includes(l.label.id),
                                    );
                                    try {
                                        onChangeLabels(newLabels); // optimistic update
                                        await Promise.all(
                                            idsToRemove.map((id) =>
                                                common.ajax(
                                                    "DELETE",
                                                    `${window.apiBasePath}/multiaccess/memberbooth/label/${id}`,
                                                    null,
                                                ),
                                            ),
                                        );
                                    } catch (err) {
                                        UIkit.notification(t("delete_failed"), {
                                            status: "danger",
                                        });
                                        onChangeLabels(labels); // revert
                                    }
                                    onChangeLabels(newLabels);
                                }}
                            />
                        </a>
                    </li>
                );
            })}
        </ul>
    );
};

const LabelsPage = ({
    member: _member,
    membership: membership,
    initialLabels,
}: {
    member: member_t;
    membership: membership_t;
    initialLabels: UploadedLabel[];
}) => {
    const { t } = useTranslation("labels");
    const [labels, setLabels] = useState(initialLabels);

    // Split labels into active and expired
    const [now, setNow] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setNow(new Date());
        }, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <>
            <Sidebar cart={null} />
            <div id="content">
                <div className="content-centering">
                    <h1>{t("page_title")}</h1>
                    <h2>{t("active_labels")}</h2>
                    <LabelsList
                        labels={labels}
                        filter={(label) =>
                            !isExpired(now, label.label, membership)
                        }
                        now={now}
                        onChangeLabels={setLabels}
                        membership={membership}
                    />
                    <h2>{t("expired_labels")}</h2>
                    <LabelsList
                        labels={labels}
                        filter={(label) =>
                            isExpired(now, label.label, membership)
                        }
                        now={now}
                        onChangeLabels={setLabels}
                        membership={membership}
                    />
                </div>
            </div>
        </>
    );
};

const future1 = LoadCurrentMemberInfo();
const future2 = LoadCurrentMembershipInfo();
const future3 = LoadCurrentLabels();

common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;

    Promise.all([future1, future2, future3] as const)
        .then(([member, membership, labels]) => {
            root.innerHTML = "";
            render(
                <LabelsPage
                    member={member}
                    membership={membership}
                    initialLabels={labels}
                />,
                root,
            );
        })
        .catch((e) => {
            // Probably Unauthorized, redirect to login page.
            if (e.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert(
                    jsx_to_string(
                        <>
                            <h2>Failed to load member info</h2>
                            <pre>{JSON.stringify(e)}</pre>
                        </>,
                    ),
                );
            }
        });
});
