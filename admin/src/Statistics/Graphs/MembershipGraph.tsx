import { Chart, ChartConfiguration } from "chart.js";
import colorbrewer from "colorbrewer";
import React, { useEffect, useState } from "react";
import { useJson } from "State/useJson";

function toPoints<T>(items: [string, T][]): { x: number; y: T }[] {
    const values = [];
    for (const item of items) {
        values.push({ x: new Date(item[0]).getTime(), y: item[1] });
    }
    return values;
}

function filterDuplicates<T extends { x: U }, U>(items: T[]): T[] {
    const newValues = [];
    for (let i = 0; i < items.length; i++) {
        if (i == 0 || items[i]!.x != items[i - 1]!.x) {
            newValues.push(items[i]!);
        }
    }
    return newValues;
}

function maxOfSeries<T extends { y: number }>(items: T[]): T | null {
    let mx = null;
    for (const item of items) {
        if (mx == null || item.y > mx.y) {
            mx = item;
        }
    }
    return mx;
}

function pointAtDate<T extends { x: K }, K>(
    items: Array<T>,
    date: K,
): T | null {
    let best = null;
    for (const item of items) {
        if (best == null || item.x <= date) {
            best = item;
        }
    }
    return best;
}

type MembershipByDate = {
    membership: [string, number][];
    labaccess: [string, number][];
};

export const MembershipGraph = () => {
    const { data } = useJson<MembershipByDate>({
        url: `/statistics/membership/by_date`,
    });
    const [container, setContainer] = React.useState<HTMLCanvasElement | null>(
        null,
    );

    const [stats, setStats] = useState<{
        base_membership: {
            current: number;
            highest: number;
            highest_date: Date;
        };
        labaccess: {
            current: number;
            highest: number;
            highest_date: Date;
        };
    } | null>(null);

    useEffect(() => {
        if (container === null || data === null) return;

        const dataMembership = filterDuplicates(toPoints(data.membership));
        const dataLabaccess = filterDuplicates(toPoints(data.labaccess));
        const today = new Date();
        const mintime = new Date();
        mintime.setFullYear(mintime.getFullYear() - 5);
        if (dataMembership.length > 0) {
            const dataStart = dataMembership[0]!.x;
            mintime.setTime(Math.max(mintime.getTime(), dataStart));
        }

        const config: ChartConfiguration<"line", { x: number; y: number }[]> = {
            type: "line",
            data: {
                datasets: [
                    {
                        label: "Base Membership",
                        backgroundColor: colorbrewer.RdYlBu[4][3],
                        borderColor: colorbrewer.RdYlBu[4][3],
                        fill: false,
                        borderJoinStyle: "round",
                        data: dataMembership,
                        yAxisID: "y_members",
                    },
                    {
                        label: "Makerspace Access",
                        backgroundColor: colorbrewer.RdYlBu[4][0],
                        borderColor: colorbrewer.RdYlBu[4][0],
                        fill: false,
                        borderJoinStyle: "round",
                        data: dataLabaccess,
                        yAxisID: "y_makerspaceAccess",
                    },
                ],
            },
            options: {
                responsive: true,
                parsing: false,
                normalized: true,
                elements: {
                    line: {
                        tension: 0,
                    },
                    point: {
                        radius: 0,
                        hoverRadius: 3,
                    },
                },
                plugins: {
                    tooltip: {
                        mode: "nearest",
                        intersect: false,
                    },
                    // title: {
                    //     display: true,
                    //     text: "Medlemsskap",
                    // },
                    zoom: {
                        zoom: {
                            mode: "x",
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true,
                            },
                        },
                        pan: {
                            mode: "x",
                        },
                    },
                    annotation: {
                        annotations: [
                            {
                                drawTime: "afterDatasetsDraw",
                                type: "line",
                                xMin: today.getTime(),
                                xMax: today.getTime(),
                                scaleID: "x-axis-0",
                                borderColor: "red",
                                borderWidth: 1,
                            },
                        ],
                    },
                },
                scales: {
                    x: {
                        type: "time",
                        min: mintime.getTime(),
                        max: today.getTime(),
                        time: {
                            tooltipFormat: "D",
                            unit: "year",
                        },
                        title: {
                            display: true,
                            text: "Date",
                        },
                    },
                    y_members: {
                        min: 0,
                        title: {
                            display: true,
                            text: "Members with Base Membership",
                        },
                    },
                    y_makerspaceAccess: {
                        type: "linear",
                        position: "right", // `axis` is determined by the position as `'y'`
                        min: 0,
                        title: {
                            display: true,
                            text: "Members with Makerspace Access",
                        },
                        grid: {
                            color: colorbrewer.RdYlBu[4][0] + "55",
                        },
                    },
                },
                animation: false,
            },
        };

        const memberstats = document.createElement("div") as HTMLDivElement;
        const highestMembership = maxOfSeries(dataMembership) || {
            x: "never",
            y: 0,
        };
        const highestLabaccess = maxOfSeries(dataLabaccess) || {
            x: "never",
            y: 0,
        };

        const currentMembership = pointAtDate(
            dataMembership,
            today.getTime(),
        ) || {
            x: today,
            y: 0,
        };
        const currentLabaccess = pointAtDate(
            dataLabaccess,
            today.getTime(),
        ) || {
            x: today,
            y: 0,
        };

        setStats({
            base_membership: {
                current: currentMembership.y,
                highest: highestMembership.y,
                highest_date: new Date(highestMembership.x),
            },
            labaccess: {
                current: currentLabaccess.y,
                highest: highestLabaccess.y,
                highest_date: new Date(highestLabaccess.x),
            },
        });

        const chart = new Chart(container, config);
        return () => {
            chart.destroy();
        };
    }, [container, data]);

    return (
        <div>
            <canvas ref={setContainer} />
            {stats !== null && (
                <>
                    <div className="uk-flex">
                        <div>
                            <dl className="uk-description-list">
                                <dt>Base Membership</dt>
                                <dd>{stats.base_membership.current}</dd>
                                <dt>Record</dt>
                                <dd>
                                    {stats.base_membership.highest} on{" "}
                                    {stats.base_membership.highest_date.toLocaleDateString()}
                                </dd>
                            </dl>
                        </div>
                        <div className="uk-margin-left">
                            <dl className="uk-description-list">
                                <dt>Makerspace Access</dt>
                                <dd>{stats.labaccess.current}</dd>
                                <dt>Record</dt>
                                <dd>
                                    {stats.labaccess.highest} on{" "}
                                    {stats.labaccess.highest_date.toLocaleDateString()}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};
