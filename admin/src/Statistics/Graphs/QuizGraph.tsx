import { Chart, ChartConfiguration } from "chart.js";
import React, { useEffect } from "react";
import { useJson } from "State/useJson";
import { TooltipLineWidth, wordWrap } from "../Charts";

interface Question {
    question: string;
}

interface Option {
    correct: boolean;
    description: string;
}
interface OptionStatistics {
    answer_count: number;
    option: Option;
}

interface QuizStatistics {
    median_seconds_to_answer_quiz: number;
    answered_quiz_member_count: number;
    questions: {
        question: Question;
        options: OptionStatistics[];
        // Number of unique members that have answered this question
        member_answer_count: number;
        incorrect_answer_fraction: number;
    }[];
}

export const QuizGraph = ({ quiz_id }: { quiz_id: number }) => {
    const { data } = useJson<QuizStatistics>({
        url: `/quiz/quiz/${quiz_id}/statistics`,
    });
    const [container, setContainer] = React.useState<HTMLCanvasElement | null>(
        null,
    );

    useEffect(() => {
        if (container !== null && data !== null) {
            // Sort questions so that the more incorrectly answered questions are at the top
            data.questions.sort(
                (a, b) =>
                    b.incorrect_answer_fraction - a.incorrect_answer_fraction,
            );

            // Sort options so that the correct options are to the left.
            for (const q of data.questions) {
                q.options.sort((a, b) => {
                    if (a.option.correct != b.option.correct)
                        return a.option.correct ? 1 : 0;

                    return b.answer_count - a.answer_count;
                });
            }

            // Maximum number of correct and incorrect alternatives for all questions
            const maxCorrect = data.questions
                .map((q) =>
                    q.options
                        .map<number>((o) => (o.option.correct ? 1 : 0))
                        .reduce((a, b) => a + b),
                )
                .reduce((a, b) => Math.max(a, b), 0);
            const maxIncorrect = data.questions
                .map((q) =>
                    q.options
                        .map<number>((o) => (o.option.correct ? 0 : 1))
                        .reduce((a, b) => a + b),
                )
                .reduce((a, b) => Math.max(a, b), 0);

            const correctColors = ["#23851E", "#289622"];
            const incorrectColors = ["#AD2727", "#C82D2D"];

            interface Dataset {
                label: string;
                backgroundColor: string;
                borderColor: string;
                data: any[];
                options: (null | OptionStatistics)[];
            }

            const incorrectDatasets: Dataset[] = [];
            const correctDatasets: Dataset[] = [];

            for (let i = 0; i < maxCorrect; i++) {
                let color =
                    correctColors[Math.min(i, correctColors.length - 1)]!;
                correctDatasets.push({
                    label: "Correct",
                    backgroundColor: color,
                    borderColor: color,
                    data: [],
                    options: [],
                });
            }
            for (let i = 0; i < maxIncorrect; i++) {
                let color =
                    incorrectColors[Math.min(i, incorrectColors.length - 1)]!;
                incorrectDatasets.push({
                    label: "Incorrect",
                    backgroundColor: color,
                    borderColor: color,
                    data: [],
                    options: [],
                });
            }

            const datasets = [...correctDatasets, ...incorrectDatasets];

            // Go through each question option and add values to the relevant datasets
            for (let qi = 0; qi < data.questions.length; qi++) {
                const q = data.questions[qi]!;
                let correct = 0;
                let incorrect = 0;

                for (const o of q.options) {
                    let datasetIndex;
                    let datasetArray;
                    if (o.option.correct) {
                        datasetIndex = correct;
                        correct++;
                        datasetArray = correctDatasets;
                    } else {
                        datasetIndex = incorrect;
                        incorrect++;
                        datasetArray = incorrectDatasets;
                    }

                    console.assert(datasetIndex < datasetArray.length);

                    datasetArray[datasetIndex]!.data.push(
                        o.answer_count / q.member_answer_count,
                    );
                    datasetArray[datasetIndex]!.options.push(o);
                }

                // Ensure all datasets have the same length to ensure question indices are not messed up.
                for (const dataset of datasets) {
                    if (dataset.data.length <= qi) {
                        dataset.data.push(0);
                        dataset.options.push(null);
                    }
                }
            }

            const config: ChartConfiguration<"bar"> = {
                type: "bar",
                data: {
                    labels: data.questions.map((q) =>
                        q.question.question.substring(
                            0,
                            Math.min(q.question.question.length, 30),
                        ),
                    ),
                    datasets: datasets,
                },
                options: {
                    indexAxis: "y",
                    plugins: {
                        title: {
                            display: true,
                            text: "Accuracy on first question attempts",
                        },
                        tooltip: {
                            position: "nearest",
                            callbacks: {
                                title: (items) => {
                                    return wordWrap(
                                        data.questions[items[0]!.dataIndex]!
                                            .question.question,
                                        TooltipLineWidth,
                                    );
                                },
                                label: (tooltipItem) => {
                                    const option =
                                        datasets[tooltipItem.datasetIndex]!
                                            .options[tooltipItem.dataIndex];
                                    if (option != null) {
                                        return wordWrap(
                                            Math.round(
                                                datasets[
                                                    tooltipItem.datasetIndex
                                                ]!.data[tooltipItem.dataIndex] *
                                                    100,
                                            ) +
                                                "%: " +
                                                option.option.description,
                                            TooltipLineWidth,
                                        );
                                    } else {
                                        return "";
                                    }
                                },
                            },
                        },
                    },
                    responsive: true,
                    scales: {
                        x: {
                            stacked: true,
                        },
                        y: {
                            stacked: true,
                        },
                    },
                },
            };

            new Chart(container, config);
        }
    }, [container, data]);

    return (
        <div>
            {data !== null && (
                <div className="uk-flex">
                    <div>
                        <dl className="uk-description-list">
                            <dt>Respondents</dt>
                            <dd>
                                <b>{data.answered_quiz_member_count}</b>
                            </dd>
                        </dl>
                    </div>
                    <div className="uk-margin-left">
                        <dl className="uk-description-list">
                            <dt>Median time to complete</dt>
                            <dd>
                                <b>
                                    {(
                                        data.median_seconds_to_answer_quiz / 60
                                    ).toFixed(1)}{" "}
                                </b>
                                minutes
                            </dd>
                        </dl>
                    </div>
                </div>
            )}
            <canvas ref={setContainer} />
        </div>
    );
};
