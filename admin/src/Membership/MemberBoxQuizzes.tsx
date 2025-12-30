import { useJson } from "Hooks/useJson";
import { useTranslation } from "i18n/hooks";
import { Link, useParams } from "react-router-dom";

interface Quiz {
    id: number;
    name: string;
    description: string;
}

interface MemberQuizStatistic {
    quiz: Quiz;
    total_questions_in_quiz: number;
    correctly_answered_questions: number;
}

function MemberBoxQuizzes() {
    const { member_id } = useParams<{ member_id: string }>();
    const { t } = useTranslation("member_quizzes");

    const { data, isLoading, error } = useJson<MemberQuizStatistic[]>({
        url: `/quiz/member/${member_id}/statistics`,
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

    if (!data || data.length === 0) {
        return (
            <div className="uk-margin-top">
                <p>{t("no_quizzes")}</p>
            </div>
        );
    }

    // Sort by completion ratio (descending)
    const sortedData = [...data].sort((a, b) => {
        const ratioA =
            a.total_questions_in_quiz > 0
                ? a.correctly_answered_questions / a.total_questions_in_quiz
                : 0;
        const ratioB =
            b.total_questions_in_quiz > 0
                ? b.correctly_answered_questions / b.total_questions_in_quiz
                : 0;
        return ratioB - ratioA;
    });

    return (
        <div className="uk-margin-top">
            <table className="uk-table uk-table-small uk-table-striped uk-table-hover">
                <thead>
                    <tr>
                        <th>{t("table.quiz")}</th>
                        <th>{t("table.correctly_answered")}</th>
                        <th>{t("table.completion")}</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedData.map((stat) => {
                        const completionPercentage =
                            stat.total_questions_in_quiz > 0
                                ? Math.round(
                                      (stat.correctly_answered_questions /
                                          stat.total_questions_in_quiz) *
                                          100,
                                  )
                                : 0;

                        const isComplete =
                            stat.total_questions_in_quiz > 0 &&
                            stat.correctly_answered_questions >=
                                stat.total_questions_in_quiz;

                        return (
                            <tr key={stat.quiz.id}>
                                <td>
                                    <Link to={`/quiz/${stat.quiz.id}`}>
                                        {stat.quiz.name}
                                    </Link>
                                </td>
                                <td>
                                    {stat.correctly_answered_questions} /{" "}
                                    {stat.total_questions_in_quiz}
                                </td>
                                <td>
                                    {isComplete ? "✅ " : ""}
                                    {completionPercentage}%
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

export default MemberBoxQuizzes;
