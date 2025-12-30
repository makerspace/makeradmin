// Shared task log entry interface (base fields)
export interface TaskLogEntry {
    id: number;
    card_id: string;
    card_name: string;
    card_url: string;
    action: string;
    created_at: string;
    labels: string[];
}

// Extended task log entry with member info (for global statistics)
export interface TaskLogEntryWithMember extends TaskLogEntry {
    member_id: number | null;
    member_name: string | null;
}

export type ActionKey =
    | "actions.assigned"
    | "actions.completed"
    | "actions.not_done_did_something_else"
    | "actions.not_done_confused"
    | "actions.not_done_forgot"
    | "actions.not_done_no_time"
    | "actions.not_done_other"
    | "actions.not_done_rerolled"
    | "actions.ignored"
    | "actions.already_completed_by_someone_else";

export const ACTION_INFO: Record<
    string,
    { key: ActionKey; isCompleted: boolean }
> = {
    assigned: { key: "actions.assigned", isCompleted: false },
    completed: { key: "actions.completed", isCompleted: true },
    not_done_did_something_else: {
        key: "actions.not_done_did_something_else",
        isCompleted: false,
    },
    not_done_confused: {
        key: "actions.not_done_confused",
        isCompleted: false,
    },
    not_done_forgot: { key: "actions.not_done_forgot", isCompleted: false },
    not_done_no_time: { key: "actions.not_done_no_time", isCompleted: false },
    not_done_other: { key: "actions.not_done_other", isCompleted: false },
    not_done_rerolled: { key: "actions.not_done_rerolled", isCompleted: false },
    ignored: { key: "actions.ignored", isCompleted: false },
    already_completed_by_someone_else: {
        key: "actions.already_completed_by_someone_else",
        isCompleted: true,
    },
};

export function formatDate(isoDate: string): string {
    const date = new Date(isoDate);
    return date.toLocaleDateString("sv-SE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export function formatDateShort(isoDate: string): string {
    const date = new Date(isoDate);
    return date.toLocaleDateString("sv-SE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    });
}
