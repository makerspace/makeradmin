import { Chart, ChartConfiguration, ChartDataset } from "chart.js";
import ButtonGroup from "Components/ButtonGroup";
import DatePeriodInput, {
    commonPeriodTemplates,
} from "Components/DatePeriodInput";
import { useJson } from "Hooks/useJson";
import { usePeriod } from "Hooks/usePeriod";
import React, { useEffect } from "react";
import { sum } from "../../utils";

type ActivityByDayOfWeek = {
    week_starts_on: "monday";
    activity: number[][];
    start_time: string | null;
    end_time: string | null;
};

enum TimeGrouping {
    Hour = "hour",
    Day = "day",
}

const TimeGroupings: TimeGrouping[] = [TimeGrouping.Hour, TimeGrouping.Day];
const TimeGroupingNames: { [key in TimeGrouping]: string } = {
    hour: "Hour",
    day: "Day",
};

export const AccessByHourGraph = ({ member_id }: { member_id?: number }) => {
    const fiveYearsAgo = new Date();
    fiveYearsAgo.setFullYear(fiveYearsAgo.getFullYear() - 5);
    const { period, lastValidPeriod } = usePeriod({
        start: fiveYearsAgo,
        end: new Date(),
    });
    const [grouping, setGrouping] = React.useState<TimeGrouping>(
        TimeGrouping.Hour,
    );
    const { data, isLoading } = useJson<ActivityByDayOfWeek>({
        url:
            member_id !== undefined
                ? `/statistics/physical_access_log/activity/by_day_of_week/member/${member_id}`
                : `/statistics/physical_access_log/activity/by_day_of_week`,
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
                        grid: {
                            offset: true,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Visits by distinct members",
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

        let labels: string[] = [];
        const days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ];
        const customTicks: number[] = [];
        for (let i = 0; i < 7; i++) {
            if (grouping === TimeGrouping.Day) {
                labels = days;
                customTicks.push(i);
            } else {
                for (let j = 0; j < 24; j++) {
                    labels.push(`${days[i]} ${j < 10 ? "0" : ""}${j}`);
                }
                // customTicks.push(i * 24 + 0);
                customTicks.push(i * 24 + 12);
            }
        }

        const dataset: ChartDataset<"bar", number[]> = {
            data:
                grouping === TimeGrouping.Day
                    ? data.activity.map((x) => sum(x, (v) => v))
                    : data.activity.flatMap((x) => x),
            label:
                member_id !== undefined ? "Days visited" : "Number of visits",
            borderColor: "#e46d22",
            backgroundColor: "#e46d22",
        };
        if (grouping === TimeGrouping.Day) {
            console.assert(dataset.data.length === 7);
        } else {
            console.assert(dataset.data.length === 7 * 24);
        }

        chart.scales["x"]!.options.afterBuildTicks = (axis) =>
            (axis.ticks = customTicks.map((v) => ({ value: v })));
        (chart.scales["x"]!.options as any).ticks.callback = (
            _value: any,
            index: number,
            _ticks: any,
        ) => days[index]!;
        chart.data.labels = labels;
        chart.data.datasets = [dataset];
        chart.update();
    }, [chart, data, grouping, isLoading]);

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
