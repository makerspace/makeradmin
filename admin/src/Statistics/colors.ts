import colorbrewer from "colorbrewer";

export const colorScale = (count: number): string[] => {
    const colors = colorbrewer.Set1[Math.max(3, Math.min(count, 9))]!;
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]!);
    }
    return result;
};

export const colorScaleSequential = (count: number): string[] => {
    const colors = colorbrewer.OrRd[Math.max(3, Math.min(count, 9))]!;
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]!);
    }
    return result;
};
