import { useJson } from "Hooks/useJson";
import { useTranslation } from "i18n/hooks";

interface OptionCount {
    option: string;
    count: number;
}

interface QuestionTypeStats {
    question_type: string;
    total_respondents: number;
    unanswered: number;
    options: OptionCount[];
}

interface MemberPreferencesResponse {
    preference_statistics: Record<string, QuestionTypeStats>;
}

// Human-readable names for question types
const QUESTION_TYPE_NAMES: Record<string, string> = {
    ROOM_PREFERENCE: "Room Preferences",
    MACHINE_PREFERENCE: "Machine Preferences",
    SKILL_LEVEL: "Self-Reported Skill Level",
    TASK_DELEGATION_ENABLED: "Task Delegation",
};

export default function MemberPreferencesPage() {
    const { t } = useTranslation("task_statistics");

    const { data, isLoading, error } = useJson<MemberPreferencesResponse>({
        url: `/tasks/statistics/member_preferences`,
    });

    if (isLoading) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("member_preferences.title")}</h2>
                <div>{t("loading")}</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("member_preferences.title")}</h2>
                <div className="uk-alert-danger">{t("error_loading")}</div>
            </div>
        );
    }

    if (!data || Object.keys(data.preference_statistics).length === 0) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("member_preferences.title")}</h2>
                <p>{t("member_preferences.no_data")}</p>
            </div>
        );
    }

    // Sort question types for consistent display order
    const sortedQuestionTypes = Object.keys(data.preference_statistics).sort();

    return (
        <div className="uk-width-1-1">
            <h2>{t("member_preferences.title")}</h2>
            <p className="uk-text-muted">
                {t("member_preferences.description")}
            </p>

            {sortedQuestionTypes.map((questionType) => {
                const stats = data.preference_statistics[questionType];
                if (!stats) return null;
                const displayName =
                    QUESTION_TYPE_NAMES[questionType] || questionType;

                return (
                    <div key={questionType} className="uk-margin-large-bottom">
                        <h3>{displayName}</h3>
                        <p className="uk-text-meta">
                            {t("member_preferences.total_respondents", {
                                count: stats.total_respondents,
                            })}
                        </p>

                        {stats.options.length === 0 &&
                        stats.unanswered === 0 ? (
                            <p className="uk-text-muted">
                                {t("member_preferences.no_responses")}
                            </p>
                        ) : (
                            <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                                <thead>
                                    <tr>
                                        <th>
                                            {t("member_preferences.option")}
                                        </th>
                                        <th style={{ width: "100px" }}>
                                            {t("member_preferences.count")}
                                        </th>
                                        <th style={{ width: "150px" }}>
                                            {t("member_preferences.percentage")}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.options.map((optionData) => {
                                        // For TASK_DELEGATION_ENABLED, include unanswered in percentage calculation (they default to enabled)
                                        // For other question types, only use total_respondents
                                        const totalMembers =
                                            questionType ===
                                            "TASK_DELEGATION_ENABLED"
                                                ? stats.total_respondents +
                                                  stats.unanswered
                                                : stats.total_respondents;
                                        const percentage =
                                            totalMembers > 0
                                                ? (
                                                      (optionData.count /
                                                          totalMembers) *
                                                      100
                                                  ).toFixed(1)
                                                : "0";

                                        return (
                                            <tr key={optionData.option}>
                                                <td>{optionData.option}</td>
                                                <td>{optionData.count}</td>
                                                <td>
                                                    <div
                                                        style={{
                                                            display: "flex",
                                                            alignItems:
                                                                "center",
                                                            gap: "8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                width: "80px",
                                                                height: "16px",
                                                                backgroundColor:
                                                                    "#e5e5e5",
                                                                borderRadius:
                                                                    "4px",
                                                                overflow:
                                                                    "hidden",
                                                            }}
                                                        >
                                                            <div
                                                                style={{
                                                                    width: `${percentage}%`,
                                                                    height: "100%",
                                                                    backgroundColor:
                                                                        "#1e87f0",
                                                                    transition:
                                                                        "width 0.3s ease",
                                                                }}
                                                            />
                                                        </div>
                                                        <span>
                                                            {percentage}%
                                                        </span>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                    {stats.unanswered > 0 &&
                                        questionType ===
                                            "TASK_DELEGATION_ENABLED" && (
                                            <tr>
                                                <td>
                                                    <em>Enabled (default)</em>
                                                </td>
                                                <td>{stats.unanswered}</td>
                                                <td>
                                                    <div
                                                        style={{
                                                            display: "flex",
                                                            alignItems:
                                                                "center",
                                                            gap: "8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                width: "80px",
                                                                height: "16px",
                                                                backgroundColor:
                                                                    "#e5e5e5",
                                                                borderRadius:
                                                                    "4px",
                                                                overflow:
                                                                    "hidden",
                                                            }}
                                                        >
                                                            <div
                                                                style={{
                                                                    width: `${(
                                                                        (stats.unanswered /
                                                                            (stats.total_respondents +
                                                                                stats.unanswered)) *
                                                                        100
                                                                    ).toFixed(
                                                                        1,
                                                                    )}%`,
                                                                    height: "100%",
                                                                    backgroundColor:
                                                                        "#1e87f0",
                                                                    transition:
                                                                        "width 0.3s ease",
                                                                }}
                                                            />
                                                        </div>
                                                        <span>
                                                            {(
                                                                (stats.unanswered /
                                                                    (stats.total_respondents +
                                                                        stats.unanswered)) *
                                                                100
                                                            ).toFixed(1)}
                                                            %
                                                        </span>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                </tbody>
                            </table>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
