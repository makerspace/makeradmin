import {
    BarController,
    BarElement,
    CategoryScale,
    Chart,
    Legend,
    LinearScale,
    LineController,
    LineElement,
    LogarithmicScale,
    PointElement,
    ScatterController,
    TimeScale,
    TimeSeriesScale,
    Title,
    Tooltip,
} from "chart.js";
import "chartjs-adapter-luxon";
import annotationPlugin from "chartjs-plugin-annotation";
import zoomPlugin from "chartjs-plugin-zoom";
import React, { useEffect } from "react";
import { get } from "../gateway";

Chart.register(
    LineElement,
    BarElement,
    PointElement,
    BarController,
    LineController,
    ScatterController,
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    TimeScale,
    TimeSeriesScale,
    Legend,
    Title,
    Tooltip,
    zoomPlugin,
    annotationPlugin,
);

export const TooltipLineWidth = 100;

export const wordWrap = (text: string, maxLength: number): string => {
    const words = text.split(" ");
    let lines = [""];
    let currentLine = 0;
    for (const word of words) {
        if (lines[currentLine]!.length + word.length > maxLength) {
            lines.push("");
            currentLine++;
        }
        lines[currentLine] += word + " ";
    }
    return lines.join("\n");
};

export function useJson<T>(url: string): {
    data: T | null;
    isLoading: boolean;
    error: any;
} {
    const [data, setData] = React.useState<T | null>(null);
    const [isLoading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    useEffect(() => {
        setLoading(true);
        get({
            url,
        })
            .then((data) => {
                setData(data.data as T);
                setLoading(false);
                setError(null);
            })
            .catch((err) => {
                setError(err);
                setData(null);
                setLoading(false);
            });
    }, [url]);

    return {
        data,
        isLoading,
        error,
    };
}
