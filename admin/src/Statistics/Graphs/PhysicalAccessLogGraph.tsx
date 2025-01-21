import { Chart, ChartConfiguration, ChartDataset } from "chart.js";
import ButtonGroup from "Components/ButtonGroup";
import DatePeriodInput, {
    commonPeriodTemplates,
} from "Components/DatePeriodInput";
import { useJson } from "Hooks/useJson";
import { usePeriod } from "Hooks/usePeriod";
import React, { useEffect } from "react";

type ActivityEntry = {
    date: string;
    count: number;
};

type PhysicalActivity = {
    start_time: string | null;
    end_time: string | null;
    activity: ActivityEntry[];
};

enum TimeGrouping {
    Day = "day",
    Week = "week",
    Month = "month",
    Year = "year",
}

const TimeGroupings: TimeGrouping[] = [
    TimeGrouping.Day,
    TimeGrouping.Week,
    TimeGrouping.Month,
    TimeGrouping.Year,
];
const TimeGroupingNames: { [key in TimeGrouping]: string } = {
    day: "Day",
    week: "Week",
    month: "Month",
    year: "Year",
};

export const PhysicalAccessLogGraph = ({
    member_id,
}: {
    member_id?: number;
}) => {
    const [grouping, setGrouping] = React.useState<TimeGrouping>(
        TimeGrouping.Month,
    );

    const fiveYearsAgo = new Date();
    fiveYearsAgo.setFullYear(fiveYearsAgo.getFullYear() - 5);
    const { period, lastValidPeriod } = usePeriod({
        start: fiveYearsAgo,
        end: new Date(),
    });
    const { data, isLoading } = useJson<PhysicalActivity>({
        url:
            member_id !== undefined
                ? `/statistics/physical_access_log/activity/by_${grouping}/member/${member_id}`
                : `/statistics/physical_access_log/activity/by_${grouping}`,
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
    const [chart, setChart] = React.useState<Chart<"bar"> | null>(null);

    useEffect(() => {
        if (container === null) return;
        if (chart !== null) return;

        const config: ChartConfiguration<"bar"> = {
            type: "bar",
            data: {
                labels: [],
                datasets: [],
            },
            options: {
                plugins: {
                    tooltip: {
                        position: "nearest",
                        mode: "index",
                        intersect: false,
                    },
                },
                scales: {
                    x: {
                        type: "time",
                        grid: {
                            offset: false,
                        },
                        time: {
                            unit: "month",
                            tooltipFormat: "D",
                            displayFormats: {
                                month: "MMM yyyy",
                                year: "yyyy",
                            },
                        },
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Number of visits",
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

        const dataset: ChartDataset<"bar", number[]> = {
            data: data.activity.map((entry) => entry.count),
            label:
                member_id !== undefined ? "Days visited" : "Number of visits",
            borderColor: "#e46d22",
            backgroundColor: "#e46d22",
        };

        chart.data.labels = data.activity.map((entry) =>
            new Date(entry.date).getTime(),
        );
        chart.data.datasets = [dataset];
        chart.options!.scales!["x"]!.grid!.offset =
            grouping === "year" || grouping === "month";
        (chart.options!.scales!["x"]! as any).time!.unit =
            grouping === "year" ? "year" : "month";
        chart.update();
    }, [chart, data, isLoading]);

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
                    <ButtonGroup
                        value={grouping}
                        onChange={setGrouping}
                        options={TimeGroupings}
                        label={(x) => TimeGroupingNames[x]}
                    />
                </div>
                <canvas ref={setContainer} />
            </div>
        </>
    );
};
