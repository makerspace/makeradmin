import { useJson } from "Hooks/useJson";
import { Translator, useTranslation } from "i18n/hooks";
import { ACTION_INFO, formatDate, TaskLogEntry } from "Models/taskActions";
import { useParams } from "react-router-dom";

interface MemberTaskInfoResponse {
    task_logs: TaskLogEntry[];
    preferred_rooms: string[] | null;
    self_reported_skill_level: string | null;
    completed_tasks_by_label: Record<string, number>;
    time_at_space_since_last_task_hours: number;
    total_completed_tasks: number;
}

function formatHours(hours: number, t_time: Translator<"time">): string {
    if (hours < 1) {
        const count = Math.round(hours * 60);
        return t_time("duration.minutes", { count });
    } else if (hours < 24) {
        const count = parseFloat(hours.toFixed(1));
        return t_time("duration.hours", { count });
    } else {
        const count = parseFloat((hours / 24).toFixed(1));
        return t_time("duration.days", { count });
    }
}

function MemberBoxTasks() {
    const { member_id } = useParams<{ member_id: string }>();
    const { t } = useTranslation("member_tasks");
    const { t: t_time } = useTranslation("time");
    const { t: t_tasks } = useTranslation("tasks");

    const { data, isLoading, error } = useJson<MemberTaskInfoResponse>({
        url: `/tasks/member/${member_id}/task_info`,
    });

    if (isLoading) {
        return <div className="uk-margin-top">{t("loading")}</div>;
    }

    if (error) {
        return (
            <div className="uk-margin-top uk-alert-danger">
                {t("error_loading")}
            </div>
        );
    }

    if (!data) {
        return (
            <div className="uk-margin-top">
                <p>{t("no_data")}</p>
            </div>
        );
    }

    const labelEntries = Object.entries(data.completed_tasks_by_label);

    return (
        <div className="uk-margin-top">
            {/* Summary info */}
            <div className="uk-grid uk-grid-small uk-child-width-1-2@m">
                <div>
                    <h3>{t("summary.title")}</h3>
                    <table className="uk-table uk-table-small uk-table-divider">
                        <tbody>
                            <tr>
                                <td>{t("summary.total_completed")}</td>
                                <td>
                                    <strong>
                                        {data.total_completed_tasks}
                                    </strong>
                                </td>
                            </tr>
                            <tr>
                                <td>{t("summary.time_at_space")}</td>
                                <td>
                                    <strong>
                                        {formatHours(
                                            data.time_at_space_since_last_task_hours,
                                            t_time,
                                        )}
                                    </strong>
                                </td>
                            </tr>
                            <tr>
                                <td>{t("summary.skill_level")}</td>
                                <td>
                                    <strong>
                                        {data.self_reported_skill_level ??
                                            t("summary.not_specified")}
                                    </strong>
                                </td>
                            </tr>
                            <tr>
                                <td>{t("summary.preferred_rooms")}</td>
                                <td>
                                    <strong>
                                        {data.preferred_rooms
                                            ? data.preferred_rooms.join(", ")
                                            : t("summary.not_specified")}
                                    </strong>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3>{t("by_label.title")}</h3>
                    {labelEntries.length > 0 ? (
                        <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                            <thead>
                                <tr>
                                    <th>{t("by_label.label")}</th>
                                    <th>{t("by_label.count")}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {labelEntries.map(([label, count]) => (
                                    <tr key={label}>
                                        <td>{label}</td>
                                        <td>{count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <p>{t("by_label.no_labels")}</p>
                    )}
                </div>
            </div>

            {/* Task history */}
            <h3>{t("history.title")}</h3>
            {data.task_logs.length > 0 ? (
                <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                    <thead>
                        <tr>
                            <th>{t("history.date")}</th>
                            <th>{t("history.task")}</th>
                            <th>{t("history.status")}</th>
                            <th>{t("history.labels")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.task_logs.map((log) => {
                            const actionMeta = ACTION_INFO[log.action];
                            const actionLabel = actionMeta
                                ? t_tasks(actionMeta.key as any)
                                : log.action;
                            const isCompleted =
                                actionMeta?.isCompleted ?? false;
                            const rowStyle = isCompleted
                                ? {}
                                : { opacity: 0.5 };

                            return (
                                <tr key={log.id} style={rowStyle}>
                                    <td style={{ whiteSpace: "nowrap" }}>
                                        {formatDate(log.created_at)}
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
                                    <td>{log.labels.join(", ")}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            ) : (
                <p>{t("history.no_tasks")}</p>
            )}
        </div>
    );
}

export default MemberBoxTasks;
