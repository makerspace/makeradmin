import { Translator } from "./i18n";

export const UnitNames = {
    mån: "month",
    år: "year",
    st: "piece",
} as const;

export const translateUnit = (
    unit: string,
    count: number,
    t: Translator<"common">,
) => {
    if (unit !== "mån" && unit !== "år" && unit !== "st")
        throw new Error(`Unexpected unit '${unit}'. Expected one of år/mån/st`);
    return t(`unit.${UnitNames[unit]}`, { count });
};
