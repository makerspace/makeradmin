import { Chart, ChartConfiguration, ChartDataset } from "chart.js";
import ButtonGroup from "Components/ButtonGroup";
import DatePeriodInput, {
    commonPeriodTemplates,
} from "Components/DatePeriodInput";
import { useJson } from "Hooks/useJson";
import { usePeriod } from "Hooks/usePeriod";
import React, { useEffect, useMemo } from "react";
import { colorScale, colorScaleSequential } from "../colors";

type RetentionTable = {
    members: RetentionMember[];
    start_time: string | null;
    end_time: string | null;
};

type RetentionMember = {
    member_id: number;
    active_months: boolean[];
    attributes: { [key: string]: string | null };
};

type SpanType = "labaccess" | "membership";
const SpanTypes: SpanType[] = ["labaccess", "membership"];
const SpanTypeNames: { [key in SpanType]: string } = {
    labaccess: "Lab access",
    membership: "Membership",
};

export const RetentionGraph = () => {
    const [spanType, setSpanType] = React.useState<SpanType>(SpanTypes[0]!);
    const [attributeType, setAttributeType] = React.useState<string | null>(
        null,
    );

    const fiveYearsAgo = new Date();
    fiveYearsAgo.setFullYear(fiveYearsAgo.getFullYear() - 5);
    const { period, lastValidPeriod } = usePeriod({
        start: fiveYearsAgo,
        end: new Date(),
    });
    const { data, isLoading } = useJson<RetentionTable>({
        url: `/statistics/retention/${spanType}`,
        params: {
            start:
                lastValidPeriod?.start?.toISOString().substring(0, 10) ??
                undefined,
            end:
                lastValidPeriod?.end?.toISOString().substring(0, 10) ??
                undefined,
        },
    });

    const [container, setContainer] = React.useState<HTMLCanvasElement | null>(
        null,
    );
    const [chart, setChart] = React.useState<Chart<"line"> | null>(null);

    const attributes = useMemo(() => {
        if (data === null) return [];
        const attributes = new Set<string>();
        for (const member of data.members) {
            for (const key in member.attributes) {
                attributes.add(key);
            }
        }
        const arr = Array.from(attributes);
        arr.sort();
        return arr;
    }, [data]);

    useEffect(() => {
        if (container === null) return;
        if (chart !== null) return;

        const config: ChartConfiguration<"line"> = {
            type: "line",
            data: {
                labels: [],
                datasets: [],
            },
            options: {
                plugins: {
                    title: {
                        display: false,
                        text: "Sales",
                    },
                    tooltip: {
                        position: "nearest",
                        // Show all items in the tooltip
                        mode: "index",
                        intersect: false,
                        // Format the tooltip as a percentage
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset!.label;
                                const value = context.parsed.y!;
                                return `${label}: ${(value * 100).toFixed(1)}%`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: "Fraction of members active",
                        },
                    },
                },
                responsive: true,
                normalized: true,
            },
        };

        const c = new Chart(container, config);
        setChart(c);

        return () => {
            c.destroy();
        };
    }, [container]);

    useEffect(() => {
        if (chart === null || data === null || isLoading) return;

        let maxLength = 0;
        const attributeValues = new Set<string | null>();
        for (const member of data.members) {
            maxLength = Math.max(maxLength, member.active_months.length);
            if (attributeType)
                attributeValues.add(member.attributes[attributeType] ?? null);
        }
        const labels = Array.from(
            { length: maxLength },
            (_, i) => `Month ${i + 1}`,
        );

        const attributeValuesArr = Array.from(attributeValues);
        attributeValuesArr.sort((a, b) =>
            a !== null && b !== null ? a.localeCompare(b) : a === null ? -1 : 1,
        );
        attributeValuesArr.push("Average");
        const colors =
            attributeType == "age_group"
                ? colorScaleSequential(attributeValuesArr.length)
                : colorScale(attributeValuesArr.length);
        const datasets: (ChartDataset<"line", number[]> & { id: string })[] =
            attributeValuesArr.map((value, i) => {
                let color = colors[i];
                if (value === null) color = "black";

                const datasetData = Array.from({ length: maxLength }, () => 0);
                let total = 0;
                for (const member of data.members) {
                    if (
                        value !== "Average" &&
                        attributeType &&
                        (member.attributes[attributeType] ?? null) !== value
                    )
                        continue;
                    total += 1;
                    for (let i = 0; i < maxLength; i++) {
                        if (member.active_months[i]!) {
                            datasetData[i]!++;
                        }
                    }
                }
                for (let i = 0; i < datasetData.length; i++) {
                    datasetData[i] = datasetData[i]! / total;
                }
                const dataset: ChartDataset<"line", number[]> & { id: string } =
                    {
                        label:
                            (value ?? "Unknown") +
                            (value === "Average" ? "" : ` (${total})`),
                        id: value ?? "Unknown",
                        data: datasetData,
                        borderColor: color,
                        backgroundColor: color,
                        // Dash the line for the average
                        borderDash: value === "Average" ? [5, 5] : [],
                        fill: false,
                        hidden: total < 10,
                    };
                return dataset;
            });

        chart.data.labels = labels;

        if (!chart.data.datasets) {
            chart.data.datasets = [];
        }
        const existingDatasets = chart.data.datasets as (ChartDataset<
            "line",
            number[]
        > & { id: string })[];
        for (const dataset of datasets) {
            const existing = existingDatasets.find((d) => d.id === dataset.id);
            if (existing) {
                existing.data = dataset.data;
                existing.hidden = dataset.hidden;
            } else {
                existingDatasets.push(dataset);
            }
        }
        chart.data.datasets = existingDatasets.filter((d) =>
            datasets.find((d2) => d2.id === d.id),
        );

        chart.update();
    }, [chart, data, isLoading, attributeType]);

    return (
        <>
            <div>
                <div className="uk-flex uk-flex-between uk-margin-top">
                    <div className="uk-flex uk-flex-middle">
                        <DatePeriodInput
                            period={period}
                            highlightChanges={false}
                            templates={commonPeriodTemplates(new Date())}
                        />
                    </div>
                    <button className="uk-button uk-button-default">
                        {attributeType
                            ? `Split by ${attributeType}`
                            : "No split"}
                    </button>
                    <div data-uk-dropdown="pos: bottom-center; delay-hide: 100">
                        <ul className="uk-nav uk-dropdown-nav">
                            <li>
                                <a onClick={() => setAttributeType(null)}>
                                    No split
                                </a>
                            </li>
                            {attributes.map((attribute) => (
                                <li
                                    key={attribute}
                                    onClick={() => setAttributeType(attribute)}
                                >
                                    <a>{attribute.replace("_", " ")}</a>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <ButtonGroup
                        value={spanType}
                        onChange={setSpanType}
                        options={SpanTypes}
                        label={(x) => SpanTypeNames[x]}
                    />
                </div>
                <canvas ref={setContainer} />
            </div>
        </>
    );
};

export const RetentionGraphExplanation = () => {
    return (
        <div className="uk-margin-bottom">
            <p>
                Shows the fraction of members who have membership after the
                given time has passed since they become members.
            </p>
            <p>
                The graph can optionally split different cohorts. In many cases
                the cohort data is not available, though.
            </p>
            <small>
                Cohort data is based on the personnummer of the member, and quiz
                responses.
            </small>
            <p>
                Only new members within the given dates will be included in the
                graph.
            </p>
        </div>
    );
};
