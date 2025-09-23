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