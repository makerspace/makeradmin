export type MessageStatus = "queued" | "sent" | "failed";

export type RecipientType = "email" | "sms";

export type MessageTemplate =
    | "labaccess_reminder"
    | "login_link"
    | "new_member"
    | "receipt"
    | "password_reset"
    | "add_labaccess_time"
    | "add_membership_time"
    | "box_warning"
    | "box_final_warning"
    | "box_terminated"
    | "quiz_first_newmember"
    | "quiz_first_oldmember"
    | "quiz_reminder"
    | "membership_reminder"
    | "new_low_income_member"
    | "gift_card_purchase"
    | "updated_member_info"
    | "memberbooth_label_report"
    | "memberbooth_label_cleaned_away"
    | "memberbooth_label_report_sms"
    | "memberbooth_label_cleaned_away_sms"
    | "memberbooth_label_expired"
    | "memberbooth_label_expiring_soon"
    | "memberbooth_box_cleaned_away"
    | "memberbooth_box_cleaned_away_sms"
    | "memberbooth_box_expired"
    | "memberbooth_box_expiring_soon";

export interface Message {
    id: number;
    subject: string;
    body: string;
    member_id: number | null;
    recipient_type: RecipientType;
    recipient: string;
    status: MessageStatus;
    template: MessageTemplate | null;
    created_at: string; // ISO date string
    updated_at: string; // ISO date string
    sent_at: string | null; // ISO date string or null
    associated_id?: number | null;
}
