import { useJson } from "Hooks/useJson";
import { useTranslation } from "i18n/hooks";
import { Link } from "react-router-dom";
import { dateToRelative } from "../utils/dateUtils";

interface CardInfo {
    card_id: string;
    card_name: string;
    card_url: string;
    first_available_at: string;
    assigned_count: number;
    completed_count: number;
    last_completed: string | null;
    last_completer_id: number | null;
    last_completer_name: string | null;
    score: number;
    overdue_days: number | null;
}

interface AllTasksResponse {
    cards: CardInfo[];
}

export default function AllTasksPage() {
    const { t } = useTranslation("task_statistics");
    const { t: t_time } = useTranslation("time");

    const { data, isLoading, error } = useJson<AllTasksResponse>({
        url: `/tasks/statistics`,
    });

    if (isLoading) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("cards.title")}</h2>
                <div>{t("loading")}</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("cards.title")}</h2>
                <div className="uk-alert-danger">{t("error_loading")}</div>
            </div>
        );
    }

    if (!data || data.cards.length === 0) {
        return (
            <div className="uk-width-1-1">
                <h2>{t("cards.title")}</h2>
                <p>{t("cards.no_cards")}</p>
            </div>
        );
    }

    // Sort cards by score descending
    const sortedCards = [...data.cards].sort((a, b) => b.score - a.score);

    return (
        <div className="uk-width-1-1">
            <h2>{t("cards.title")}</h2>

            <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                <thead>
                    <tr>
                        <th>{t("cards.task")}</th>
                        <th>{t("cards.completed_count")}</th>
                        <th>{t("cards.last_completed")}</th>
                        <th>{t("cards.last_completer")}</th>
                        <th>{t("cards.overdue")}</th>
                        <th>{t("cards.score")}</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedCards.map((card) => (
                        <tr key={card.card_id}>
                            <td>
                                <a
                                    href={card.card_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    {card.card_name}
                                </a>
                            </td>
                            <td>{card.completed_count}</td>
                            <td style={{ whiteSpace: "nowrap" }}>
                                {card.last_completed
                                    ? dateToRelative(
                                          new Date(),
                                          new Date(card.last_completed),
                                          t_time,
                                          "relative_generic",
                                      )
                                    : t("cards.never")}
                            </td>
                            <td>
                                {card.last_completer_id ? (
                                    <Link
                                        to={`/membership/members/${card.last_completer_id}/tasks`}
                                    >
                                        {card.last_completer_name}
                                    </Link>
                                ) : (
                                    "-"
                                )}
                            </td>
                            <td>
                                {card.overdue_days !== null
                                    ? t_time("duration.days", {
                                          count: Math.round(card.overdue_days),
                                      })
                                    : "-"}
                            </td>
                            <td>{card.score}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
