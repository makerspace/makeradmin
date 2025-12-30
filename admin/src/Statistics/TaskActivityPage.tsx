import { useJson } from "Hooks/useJson";
import { useTranslation } from "i18n/hooks";
import {
    ACTION_INFO,
    formatDate,
    TaskLogEntryWithMember,
} from "Models/taskActions";
import { Link } from "react-router-dom";

interface TaskActivityResponse {
    task_logs: TaskLogEntryWithMember[];
}

function extractRoom(labels: string[]): string | null {
    for (const label of labels) {
        if (label.startsWith("Room: ")) {
            return label.substring(6);
        }
    }
    return null;
}

export default function TaskActivityPage() {
    const { t } = useTranslation("task_statistics");
    const { t: t_tasks } = useTranslation("tasks");

    const { data, isLoading, error } = useJson<TaskActivityResponse>({
        url: `/tasks/statistics`,
    });

    if (isLoading) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("task_log.title")}</h2>
                <div>{t("loading")}</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("task_log.title")}</h2>
                <div className="uk-alert-danger">{t("error_loading")}</div>
            </div>
        );
    }

    if (!data || data.task_logs.length === 0) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("task_log.title")}</h2>
                <p>{t("task_log.no_logs")}</p>
            </div>
        );
    }

    // Sort task logs: completed first, then by date
    const sortedTaskLogs = [...data.task_logs].sort((a, b) => {
        const aCompleted = ACTION_INFO[a.action]?.isCompleted ?? false;
        const bCompleted = ACTION_INFO[b.action]?.isCompleted ?? false;
        if (aCompleted !== bCompleted) {
            return aCompleted ? -1 : 1;
        }
        return (
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    });

    return (
        <div className="uk-width-1-1">
            <h2>{t("task_log.title")}</h2>

            <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                <thead>
                    <tr>
                        <th>{t("task_log.date")}</th>
                        <th>{t("task_log.member")}</th>
                        <th>{t("task_log.task")}</th>
                        <th>{t("task_log.status")}</th>
                        <th>{t("task_log.room")}</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedTaskLogs.map((log) => {
                        const actionMeta = ACTION_INFO[log.action];
                        const actionLabel = actionMeta
                            ? t_tasks(actionMeta.key as any)
                            : log.action;
                        const isCompleted = actionMeta?.isCompleted ?? false;
                        const rowStyle = isCompleted ? {} : { opacity: 0.5 };

                        return (
                            <tr key={log.id} style={rowStyle}>
                                <td style={{ whiteSpace: "nowrap" }}>
                                    {formatDate(log.created_at)}
                                </td>
                                <td>
                                    {log.member_id ? (
                                        <Link
                                            to={`/membership/members/${log.member_id}/tasks`}
                                        >
                                            {log.member_name}
                                        </Link>
                                    ) : (
                                        "-"
                                    )}
                                </td>
                                <td>
                                    <a
                                        href={log.card_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        {log.card_name}
                                    </a>
                                </td>
                                <td style={{ whiteSpace: "nowrap" }}>
                                    {isCompleted ? "✅ " : ""}
                                    {actionLabel}
                                </td>
                                <td>{extractRoom(log.labels) || "-"}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
