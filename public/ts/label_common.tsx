import { useState } from "preact/hooks";
import { Translator, useTranslation } from "./i18n";
import { membership_t } from "./member_common";
declare var UIkit: any;

export const MEMBERBOX_DAYS_ALLOWED_TO_KEEP_AFTER_LABACCESS_ENDS = 45;
export const TERMINATION_WARNING_DAYS_TO_CLEANOUT = 14;

export interface UploadedLabel {
    public_url: string;
    label: MemberboothLabel;
}

export interface LabelBase {
    id: number;
    created_by_member_number: number;
    member_number: number;
    member_name: string;
    created_at: string; // ISO datetime string
    version: 3;
}

export interface TemporaryStorageLabel extends LabelBase {
    type: "TemporaryStorageLabel";
    description: string;
    expires_at: string; // ISO date string
}

export interface BoxLabel extends LabelBase {
    type: "BoxLabel";
}

export interface FireSafetyLabel extends LabelBase {
    type: "FireSafetyLabel";
    expires_at: string; // ISO date string
}

export interface Printer3DLabel extends LabelBase {
    type: "Printer3DLabel";
}

export interface NameTag extends LabelBase {
    type: "NameTag";
    membership_expires_at: string | null; // ISO date string or null
}

export interface MeetupNameTag extends LabelBase {
    type: "MeetupNameTag";
}

export interface DryingLabel extends LabelBase {
    type: "DryingLabel";
    expires_at: string; // ISO datetime string
}

export type MemberboothLabel =
    | TemporaryStorageLabel
    | BoxLabel
    | FireSafetyLabel
    | Printer3DLabel
    | NameTag
    | MeetupNameTag
    | DryingLabel;

export const DeleteButton = ({
    labelId,
    onDelete,
}: {
    labelId: number;
    onDelete: (labelId: number) => Promise<void>;
}) => {
    const { t } = useTranslation("labels");
    const [confirm, setConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const handleClick = async (e: any) => {
        e.preventDefault();
        if (!confirm) {
            setConfirm(true);
            return;
        }
        setLoading(true);
        try {
            await onDelete(labelId);
        } finally {
            setLoading(false);
        }
    };
    return (
        <button
            type="button"
            className={`uk-button confirm-button uk-icon ${
                confirm ? "confirm uk-button-danger" : ""
            }`}
            uk-icon="trash"
            title={t("delete_label")}
            disabled={loading}
            onClick={handleClick}
        >
            <span>Confirm</span>
        </button>
    );
};

export const labelExpiryDate = (
    label: MemberboothLabel,
    membership: membership_t | null,
): Date | null => {
    if ("expires_at" in label) {
        return new Date(label.expires_at);
    } else if (label.type === "NameTag" || label.type === "MeetupNameTag") {
        if (membership && membership.membership_end) {
            return membership.membership_end
                ? new Date(membership.membership_end)
                : null;
        }
    } else if (label.type == "BoxLabel") {
        if (membership && membership.labaccess_end) {
            const expiry = new Date(membership.labaccess_end);
            expiry.setDate(
                expiry.getDate() +
                    MEMBERBOX_DAYS_ALLOWED_TO_KEEP_AFTER_LABACCESS_ENDS,
            );
            return expiry;
        }
    }
    return null;
};

export const isExpired = (
    now: Date,
    label: MemberboothLabel,
    membership: membership_t | null,
) => {
    const expires_at = labelExpiryDate(label, membership);
    return expires_at ? expires_at.getTime() < now.getTime() : false;
};

const maxRelativeDays = 7;

export const expiresSoon = (
    now: Date,
    label: MemberboothLabel,
    membership: membership_t | null,
) => {
    const expires_at = labelExpiryDate(label, membership);
    if (expires_at) {
        const diff = expires_at.getTime() - now.getTime();
        return diff < 14 * 24 * 60 * 60 * 1000 && diff > 0;
    }
    return false;
};

export const expiredRecently = (
    now: Date,
    label: MemberboothLabel,
    membership: membership_t | null,
) => {
    const recentDays = label.type === "DryingLabel" ? 5 : maxRelativeDays;
    const expires_at = labelExpiryDate(label, membership);
    if (expires_at) {
        const diff = now.getTime() - expires_at.getTime();
        return diff < recentDays * 24 * 60 * 60 * 1000 && diff > 0;
    }
    return false;
};

export const dateToRelative = (
    now: Date,
    date: Date,
    t: Translator<"labels">,
    mode: "expiry" | "drying" | "generic",
) => {
    const diffMs = date.getTime() - now.getTime();
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);

    // Show relative if within ±maxRelativeDays days
    if (Math.abs(diffDay) < maxRelativeDays) {
        if (diffDay === 0) {
            if (Math.abs(diffHour) < 24) {
                if (diffHour === 0) {
                    if (Math.abs(diffMin) < 60) {
                        if (diffMin === 0) {
                            return t(`relative_${mode}.now`);
                        }
                        return t(
                            diffMin > 0
                                ? `relative_${mode}.in_minutes`
                                : `relative_${mode}.minutes_ago`,
                            { count: Math.abs(diffMin) },
                        );
                    }
                    return t(
                        diffHour > 0
                            ? `relative_${mode}.in_hours`
                            : `relative_${mode}.hours_ago`,
                        { count: Math.abs(diffHour) },
                    );
                }
                return t(
                    diffHour > 0
                        ? `relative_${mode}.in_hours`
                        : `relative_${mode}.hours_ago`,
                    { count: Math.abs(diffHour) },
                );
            }
            return t(
                diffDay > 0
                    ? `relative_${mode}.in_days`
                    : `relative_${mode}.days_ago`,
                { count: Math.abs(diffDay) },
            );
        }
        return t(
            diffDay > 0
                ? `relative_${mode}.in_days`
                : `relative_${mode}.days_ago`,
            { count: Math.abs(diffDay) },
        );
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
    const date_str = date.toLocaleString(undefined, options);
    return date.getTime() < now.getTime()
        ? t(`relative_${mode}.date_past`, { date: date_str })
        : t(`relative_${mode}.date_future`, { date: date_str });
};
