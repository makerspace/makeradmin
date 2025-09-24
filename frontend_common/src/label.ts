import { membership_t } from "./membership";

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

export const labelExpiryDate = (
    label: MemberboothLabel,
    membership: membership_t | null,
): Date | null => {
    if ("expires_at" in label) {
        return new Date(label.expires_at);
    } else if (label.type === "NameTag" || label.type === "MeetupNameTag") {
        if (membership && membership.effective_labaccess_end) {
            return membership.effective_labaccess_end
                ? new Date(membership.effective_labaccess_end)
                : null;
        }
    } else if (label.type == "BoxLabel") {
        if (membership && membership.effective_labaccess_end) {
            const expiry = new Date(membership.effective_labaccess_end);
            expiry.setDate(
                expiry.getDate() +
                    MEMBERBOX_DAYS_ALLOWED_TO_KEEP_AFTER_LABACCESS_ENDS,
            );
            return expiry;
        }
    }
    return null;
};

export const labelIsExpired = (
    now: Date,
    label: MemberboothLabel,
    membership: membership_t | null,
) => {
    const expires_at = labelExpiryDate(label, membership);
    return expires_at ? expires_at.getTime() < now.getTime() : false;
};

export const LabelMaxRelativeDays = 7;

export const labelExpiresSoon = (
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

export const labelExpiredRecently = (
    now: Date,
    label: MemberboothLabel,
    membership: membership_t | null,
) => {
    const recentDays = label.type === "DryingLabel" ? 5 : LabelMaxRelativeDays;
    const expires_at = labelExpiryDate(label, membership);
    if (expires_at) {
        const diff = now.getTime() - expires_at.getTime();
        return diff < recentDays * 24 * 60 * 60 * 1000 && diff > 0;
    }
    return false;
};
