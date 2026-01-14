import { useJson } from "Hooks/useJson";
import { useTranslation } from "i18n/hooks";
import { useState } from "react";
import { Link } from "react-router-dom";
import MemberSelect, { MemberOption } from "../Components/MemberSelect";
import { dateToRelative } from "../utils/dateUtils";
import { post } from "../gateway";
import { showSuccess, showError } from "../message";
import UIkit from "uikit";

interface ScoreOperation {
    operation: "add" | "multiply" | "set";
    value: number;
    description: string;
}

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
    cannot_be_assigned_reason: string | null;
    score_calculation: ScoreOperation[];
}

interface AllTasksResponse {
    cards: CardInfo[];
    member_id: number | null;
}

function ScoreCalculationDetails({
    calculation,
}: {
    calculation: ScoreOperation[];
}) {
    let currentScore = 0;

    return (
        <div style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
            <table
                className="uk-table uk-table-small uk-table-divider"
                style={{ marginBottom: 0 }}
            >
                <thead>
                    <tr>
                        <th style={{ width: "3rem" }}>Op</th>
                        <th style={{ width: "5rem" }}>Value</th>
                        <th>Description</th>
                        <th style={{ width: "6rem", textAlign: "right" }}>
                            Score
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {calculation.map((op, index) => {
                        let opSymbol: string;
                        if (op.operation === "add") {
                            currentScore += op.value;
                            opSymbol = "+";
                        } else if (op.operation === "multiply") {
                            currentScore *= op.value;
                            opSymbol = "×";
                        } else {
                            currentScore = op.value;
                            opSymbol = "=";
                        }

                        return (
                            <tr key={index}>
                                <td>{opSymbol}</td>
                                <td>{op.value.toFixed(2)}</td>
                                <td>{op.description}</td>
                                <td style={{ textAlign: "right" }}>
                                    {currentScore.toFixed(2)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

export default function AllTasksPage() {
    const { t } = useTranslation("task_statistics");
    const { t: t_time } = useTranslation("time");
    const [selectedMember, setSelectedMember] = useState<MemberOption | null>(
        null,
    );
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null);
    const [assigningCardId, setAssigningCardId] = useState<string | null>(null);
    const [modalSelectedMember, setModalSelectedMember] =
        useState<MemberOption | null>(null);

    const { data, isLoading, error, refresh } = useJson<AllTasksResponse>({
        url: `/tasks/statistics`,
        params: selectedMember
            ? { member_id: selectedMember.member_id }
            : { member_id: undefined },
    });

    const handleAssignTask = async (
        cardId: string,
        cardName: string,
        memberToAssign: MemberOption | null,
    ) => {
        if (!memberToAssign) {
            // Show member selection modal
            setAssigningCardId(cardId);
            setModalSelectedMember(null); // Reset modal selection
            const modal = UIkit.modal("#assign-task-modal");
            modal.show();
            return;
        }

        // Assign the task directly if member is already selected
        try {
            await post({
                url: `/tasks/assign`,
                data: {
                    card_id: cardId,
                    member_id: memberToAssign.member_id,
                    ignore_reasons: [],
                },
                expectedDataStatus: null,
            });
            showSuccess(
                `Task "${cardName}" has been assigned to ${memberToAssign.firstname} ${memberToAssign.lastname}`,
            );
            refresh();
        } catch (err) {
            showError(`Failed to assign task: ${err}`);
        }
    };

    const handleModalAssign = async () => {
        if (!assigningCardId || !modalSelectedMember) {
            return;
        }

        const card = data?.cards.find((c) => c.card_id === assigningCardId);
        if (!card) return;

        try {
            await post({
                url: `/tasks/assign`,
                data: {
                    card_id: assigningCardId,
                    member_id: modalSelectedMember.member_id,
                    ignore_reasons: [],
                },
                expectedDataStatus: null,
            });
            showSuccess(
                `Task "${card.card_name}" has been assigned to ${modalSelectedMember.firstname} ${modalSelectedMember.lastname}`,
            );
            UIkit.modal("#assign-task-modal").hide();
            setAssigningCardId(null);
            setModalSelectedMember(null);
            refresh();
        } catch (err) {
            showError(`Failed to assign task: ${err}`);
        }
    };

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

            <div className="uk-margin-bottom uk-form-stacked">
                <label className="uk-form-label" htmlFor="member-select">
                    {t("cards.score_for_member")}
                </label>
                <div className="uk-form-controls">
                    <MemberSelect
                        name="member-select"
                        placeholder={t("cards.search_member_placeholder")}
                        value={selectedMember}
                        onChange={setSelectedMember}
                    />
                </div>
                {selectedMember && (
                    <p className="uk-text-muted uk-margin-small-top">
                        {t("cards.showing_scores_for_member", {
                            name: `${selectedMember.firstname} ${selectedMember.lastname || ""}`,
                        })}
                    </p>
                )}
            </div>

            {/* Modal for assigning task to a member */}
            <div id="assign-task-modal" uk-modal="container: false">
                <div className="uk-modal-dialog uk-modal-body">
                    <button
                        className="uk-modal-close-default"
                        type="button"
                        uk-close=""
                    ></button>
                    <h2 className="uk-modal-title">
                        {t("cards.assign_task_modal_title")}
                    </h2>
                    <div className="uk-margin">
                        <label className="uk-form-label">
                            {t("cards.select_member_to_assign")}
                        </label>
                        <MemberSelect
                            name="assign-member-select"
                            placeholder={t("cards.search_member_placeholder")}
                            value={modalSelectedMember}
                            onChange={setModalSelectedMember}
                        />
                    </div>
                    <div className="uk-modal-footer uk-text-right">
                        <button
                            className="uk-button uk-button-default uk-modal-close"
                            type="button"
                        >
                            {t("cards.cancel")}
                        </button>
                        <button
                            className="uk-button uk-button-primary"
                            type="button"
                            onClick={handleModalAssign}
                            disabled={!modalSelectedMember}
                        >
                            {t("cards.assign")}
                        </button>
                    </div>
                </div>
            </div>

            <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                <thead>
                    <tr>
                        <th>{t("cards.task")}</th>
                        <th>{t("cards.completed_count")}</th>
                        <th>{t("cards.last_completed")}</th>
                        <th>{t("cards.last_completer")}</th>
                        <th>{t("cards.overdue")}</th>
                        <th>{t("cards.score")}</th>
                        {selectedMember && <th>{t("cards.status")}</th>}
                        <th>{t("cards.actions")}</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedCards.map((card) => (
                        <>
                            <tr
                                key={card.card_id}
                                className={
                                    card.cannot_be_assigned_reason
                                        ? "uk-text-muted"
                                        : ""
                                }
                                onClick={() =>
                                    setExpandedCardId(
                                        expandedCardId === card.card_id
                                            ? null
                                            : card.card_id,
                                    )
                                }
                                style={{ cursor: "pointer" }}
                            >
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
                                              count: Math.round(
                                                  card.overdue_days,
                                              ),
                                          })
                                        : "-"}
                                </td>
                                <td>{card.score}</td>
                                {selectedMember && (
                                    <td>
                                        {card.cannot_be_assigned_reason ? (
                                            <span
                                                className="uk-text-danger"
                                                title={
                                                    card.cannot_be_assigned_reason
                                                }
                                            >
                                                ✗{" "}
                                                {card.cannot_be_assigned_reason
                                                    .length > 40
                                                    ? card.cannot_be_assigned_reason.substring(
                                                          0,
                                                          40,
                                                      ) + "..."
                                                    : card.cannot_be_assigned_reason}
                                            </span>
                                        ) : (
                                            <span className="uk-text-success">
                                                ✓
                                            </span>
                                        )}
                                    </td>
                                )}
                                <td>
                                    <button
                                        className="uk-button uk-button-small uk-button-primary"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleAssignTask(
                                                card.card_id,
                                                card.card_name,
                                                selectedMember,
                                            );
                                        }}
                                    >
                                        {t("cards.assign_to_member")}
                                    </button>
                                </td>
                            </tr>
                            {expandedCardId === card.card_id && (
                                <tr key={`${card.card_id}-details`}>
                                    <td
                                        colSpan={selectedMember ? 8 : 7}
                                        style={{
                                            padding: "0.5rem 1rem",
                                            backgroundColor: "#f8f8f8",
                                        }}
                                    >
                                        <ScoreCalculationDetails
                                            calculation={card.score_calculation}
                                        />
                                    </td>
                                </tr>
                            )}
                        </>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
