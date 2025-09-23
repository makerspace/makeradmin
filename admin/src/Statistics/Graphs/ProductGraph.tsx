import { Chart, ChartConfiguration, ChartDataset } from "chart.js";
import "chartjs-adapter-luxon";
import ButtonGroup from "Components/ButtonGroup";
import DatePeriodInput, {
    commonPeriodTemplates,
} from "Components/DatePeriodInput";
import { RequestParams } from "gateway";
import { CacheGetter, DataCache, useDataCache } from "Hooks/useDataCache";
import { usePeriod } from "Hooks/usePeriod";
import React, { useCallback, useEffect, useMemo } from "react";
import Select from "react-select";
import _ from "underscore";
import DatePeriod from "../../Models/DatePeriod";
import { copyArray, sum } from "../../utils";
import { colorScale } from "../colors";
import { Product, ProductCategory, SalesResponse } from "../types";

const matchesFilter = (name: string, filter: string) => {
    return name.toLowerCase().trim().includes(filter);
};

const flattenSelectionToProducts = (selected: SelectItem[]) => {
    return Array.from(
        new Set(
            selected.flatMap((p) =>
                p.type == "category" ? p.category.items : [p.product],
            ),
        ),
    );
};

const ValueTypes = ["amount", "count"] as const;
type ValueType = (typeof ValueTypes)[number];

const ValueTypeNames: { [key in ValueType]: string } = {
    amount: "Amount",
    count: "Units sold",
};

const DateGroupings = ["day", "week", "month", "total"] as const;
type DateGrouping = (typeof DateGroupings)[number];

const DateGroupingNames: { [key in DateGrouping]: string } = {
    day: "Day",
    week: "Week",
    month: "Month",
    total: "Total",
};

const MillisecondsPerWeek = 1000 * 60 * 60 * 24 * 7;
const DateGroupingKey: { [key in DateGrouping]: (d: Date) => string | number } =
    {
        day: (d) => d.toDateString(),
        week: (d) => Math.floor(d.getTime() / MillisecondsPerWeek),
        month: (d) => `${d.getFullYear()}-${d.getMonth()}`,
        total: (_d) => 0,
    };

const DateGroupingKeyToDate: {
    [key in DateGrouping]: (key: string | number) => Date;
} = {
    day: (key) => new Date(key as string),
    week: (key) => new Date((key as number) * MillisecondsPerWeek),
    month: (key) => {
        const [year, month] = (key as string).split("-");
        return new Date(parseInt(year!), parseInt(month!));
    },
    total: (_key) => new Date(),
};

const groupReducer = <T, K, G>(
    items: T[],
    key: (item: T) => K,
    combine: (key: K, items: T[]) => G,
) => {
    if (items.length == 0) return [];
    const groups = [];
    let currentKey = key(items[0]!);
    let startIndex = 0;
    for (let i = 0; i < items.length; i++) {
        const item = items[i]!;
        const k = key(item);
        if (k != currentKey) {
            groups.push(combine(currentKey, items.slice(startIndex, i)));
            currentKey = k;
            startIndex = i;
        }
    }
    groups.push(combine(currentKey, items.slice(startIndex)));
    return groups;
};

type ChartMeta = {
    lastDataMin: Date | undefined;
    lastDataMax: Date | undefined;
    lastGrouping: DateGrouping | undefined;
};

const RenderProductGraphByTime = <T,>(
    chart: Chart<"bar"> | null,
    cache: CacheGetter<T, SalesResponse>,
    items: T[],
    itemLabel: (item_id: number) => string,
    grouping: DateGrouping,
    valueType: ValueType,
    period: DatePeriod,
    hiddenItemIds: number[],
) => {
    if (chart === null) return;

    const data = items
        .map((p) => cache(p))
        .filter((d) => d != null) as SalesResponse[];
    if (valueType == "amount") {
        data.sort((a, b) => b.total_amount - a.total_amount);
    } else {
        data.sort((a, b) => b.total_count - a.total_count);
    }

    if (data.length == 0) {
        chart.data.datasets = [];
        chart.data.labels = [];
        chart.update();
        return;
    }

    const nonEmptyData = data.filter((d) => d.by_date.length > 0);
    const allDays = [];

    if (nonEmptyData.length > 0) {
        const minDate = nonEmptyData
            .map((d) => new Date(d.by_date[0]!.date))
            .reduce((a, b) => (a < b ? a : b));
        const maxDate = nonEmptyData
            .map((d) => new Date(d.by_date[d.by_date.length - 1]!.date))
            .reduce((a, b) => (a > b ? a : b));
        for (
            let d = new Date(minDate);
            d <= maxDate;
            d.setDate(d.getDate() + 1)
        ) {
            allDays.push(new Date(d));
        }
    }

    const dateToGroup = DateGroupingKey[grouping];
    const groupToDate = DateGroupingKeyToDate[grouping];
    const allDates = groupReducer(allDays, dateToGroup, (key, _) =>
        groupToDate(key),
    );

    const colors = colorScale(data.length);
    const datasets = data.map((d, datasetIndex) => {
        const grouped = groupReducer(
            d.by_date,
            (s) => dateToGroup(new Date(s.date)),
            (key, items) => ({
                date: groupToDate(key),
                amount: sum(items, (s) => s.amount),
                count: sum(items, (s) => s.count),
            }),
        );

        const data = [];
        let index = 0;
        for (const date of allDates) {
            if (
                index < grouped.length &&
                grouped[index]!.date.getTime() == date.getTime()
            ) {
                data.push(
                    valueType === "amount"
                        ? grouped[index]!.amount
                        : grouped[index]!.count,
                );
                index++;
            } else {
                data.push(0);
            }
        }

        let dataset: ChartDataset<"bar", number[]> & { id: number } = {
            id: d.id,
            data,
            label: itemLabel(d.id) + (d.total_amount == 0 ? " (no sales)" : ""),
            backgroundColor: colors[datasetIndex],
            hidden: hiddenItemIds.includes(d.id),
        };
        return dataset;
    });

    // Update the chart.
    // To make animations work properly, we have to preserve the old dataset objects
    const newDatasets = chart.data.datasets.filter(
        (d) => datasets.find((d2) => d2.id == (d as any).id) !== undefined,
    );

    const chartMeta = chart as any as ChartMeta;

    const newMin = allDates[0];
    const newMax = allDates[allDates.length - 1];
    const startMoved = chartMeta.lastDataMin?.getTime() != newMin?.getTime();
    const endMoved = chartMeta.lastDataMax?.getTime() != newMax?.getTime();
    const groupingChanged = chartMeta.lastGrouping != grouping;
    chartMeta.lastDataMin = newMin;
    chartMeta.lastDataMax = newMax;
    chartMeta.lastGrouping = grouping;

    for (const d of datasets) {
        const existing = newDatasets.find((d2) => (d2 as any).id == d.id);
        if (existing === undefined) {
            newDatasets.push(d);
        } else {
            // Assume only the data changes
            // We must re-use the existing array to make the animation work
            // Chartjs has special listeners for the shift, unshift, pop and push methods
            if (startMoved) {
                while (existing.data.length < d.data.length) {
                    existing.data.unshift(0);
                }
                while (existing.data.length > d.data.length) {
                    existing.data.shift();
                }
            }

            if (endMoved) {
                while (existing.data.length < d.data.length) {
                    existing.data.push(0);
                }
                while (existing.data.length > d.data.length) {
                    existing.data.pop();
                }
            }

            existing.label = d.label;
            existing.backgroundColor = d.backgroundColor;
            existing.borderColor = d.borderColor;
            existing.hidden = d.hidden;

            if (groupingChanged) {
                // We want chartjs to treat this as completely new data
                existing.data = d.data;
            } else {
                copyArray(d.data, existing.data);
            }
        }
    }
    chart.data.datasets = newDatasets;
    chart.data.labels = allDates;
    chart.config.options!.scales!["y"]!.title!.text =
        "Sales" +
        (valueType == "amount"
            ? data.length > 0
                ? ` [${data[0]!.amount_unit}]`
                : ""
            : " [units]");
    chart.config.options!.scales!["x"]!.suggestedMin = period.start
        ?.toISOString()
        .substring(0, 10);
    chart.config.options!.scales!["x"]!.suggestedMax = period.end
        ?.toISOString()
        .substring(0, 10);
    chart.update();
};

const ProductGraphByTime = <T,>({
    items,
    itemLabel,
    grouping,
    cache,
    valueType,
    period,
    hiddenItemIds,
    onChangeHiddenItemIds,
}: {
    items: T[];
    grouping: DateGrouping;
    cache: DataCache<T, SalesResponse>;
    valueType: ValueType;
    period: DatePeriod;
    itemLabel: (item_id: number) => string;
    hiddenItemIds: number[];
    onChangeHiddenItemIds: (
        update: (hiddenItemIds: number[]) => number[],
    ) => void;
}) => {
    const [container, setContainer] = React.useState<HTMLCanvasElement | null>(
        null,
    );
    const [chart, setChart] = React.useState<Chart<"bar"> | null>(null);
    const render = useCallback(_.debounce(RenderProductGraphByTime, 500), []);

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
                indexAxis: "x",
                plugins: {
                    title: {
                        display: false,
                        text: "Sales",
                    },
                    tooltip: {
                        position: "nearest",
                    },
                    legend: {
                        onClick: (_evt, legendItem, legend) => {
                            const datasetId = (
                                legend.chart.data.datasets[
                                    legendItem.datasetIndex!
                                ] as any
                            ).id;
                            onChangeHiddenItemIds((prev) => {
                                if (prev.includes(datasetId)) {
                                    return prev.filter(
                                        (id) => id !== datasetId,
                                    );
                                } else {
                                    return [...prev, datasetId];
                                }
                            });
                        },
                    },
                },
                responsive: true,
                normalized: true,
                scales: {
                    x: {
                        stacked: true,
                        type: "time",
                        time: {
                            unit: "month",
                            tooltipFormat: "D",
                            displayFormats: {
                                day: "MMM yyyy",
                                week: "MMM yyyy",
                                month: "MMM yyyy",
                            },
                        },
                    },
                    y: {
                        stacked: true,
                        title: {
                            display: true,
                            text: "",
                        },
                    },
                },
                animations: {
                    x: { duration: 500 },
                    y: { duration: 500 },
                },
            },
        };

        const c = new Chart(container, config);
        setChart(c);

        return () => {
            c.destroy();
            render.cancel();
        };
    }, [container]);

    // Render the graph after a timeout, while loading data
    useEffect(() => {
        if (cache.isLoading) {
            render(
                chart,
                cache.cache,
                items,
                itemLabel,
                grouping,
                valueType,
                period,
                hiddenItemIds,
            );
        } else {
            // Render immediately if we already have the data
            render.cancel();
            RenderProductGraphByTime(
                chart,
                cache.cache,
                items,
                itemLabel,
                grouping,
                valueType,
                period,
                hiddenItemIds,
            );
        }
    }, [
        chart,
        cache.cache,
        cache.version,
        cache.isLoading,
        container,
        items,
        itemLabel,
        valueType,
        hiddenItemIds,
    ]);

    return <canvas ref={setContainer} />;
};

const RenderProductGraphByTotal = <T,>(
    chart: Chart<"bar"> | null,
    cache: CacheGetter<T, SalesResponse>,
    items: T[],
    itemLabel: (item_id: number) => string,
    valueType: ValueType,
    hiddenItemIds: number[],
) => {
    if (chart === null) return;

    const data = items
        .map((p) => cache(p))
        .filter((d) => d != null) as SalesResponse[];
    if (valueType == "amount") {
        data.sort((a, b) => b.total_amount - a.total_amount);
    } else {
        data.sort((a, b) => b.total_count - a.total_count);
    }

    if (data.length == 0) {
        chart.data.datasets = [];
        chart.data.labels = [];
        chart.update();
        return;
    }

    const colors = colorScale(data.length);
    const datasets = data.map((d, datasetIndex) => {
        let dataset: ChartDataset<"bar", number[]> & { id: number } = {
            id: d.id,
            data: [valueType == "amount" ? d.total_amount : d.total_count],
            label: itemLabel(d.id) + (d.total_amount == 0 ? " (no sales)" : ""),
            backgroundColor: colors[datasetIndex],
            hidden: hiddenItemIds.includes(d.id),
        };
        return dataset;
    });

    // Update the chart.
    // To make animations work properly, we have to preserve the old dataset objects
    const newDatasets = chart.data.datasets.filter(
        (d) => datasets.find((d2) => d2.id == (d as any).id) !== undefined,
    );
    for (const d of datasets) {
        const existing = newDatasets.find((d2) => (d2 as any).id == d.id);
        if (existing === undefined) {
            newDatasets.push(d);
        } else {
            // Assume only the data and label changes
            existing.data = d.data;
            existing.label = d.label;
            existing.backgroundColor = d.backgroundColor;
            existing.borderColor = d.borderColor;
            existing.hidden = d.hidden;
        }
    }
    chart.data.datasets = newDatasets;
    chart.data.labels = ["Total"];
    chart.config.options!.scales!["y"]!.title!.text =
        "Sales" +
        (valueType == "amount"
            ? data.length > 0
                ? ` [${data[0]!.amount_unit}]`
                : ""
            : " [units]");
    chart.update();
};

const ProductGraphByTotal = <T,>({
    items,
    itemLabel,
    cache,
    valueType,
    hiddenItemIds,
    onChangeHiddenItemIds,
}: {
    items: T[];
    itemLabel: (item_id: number) => string;
    cache: DataCache<T, SalesResponse>;
    valueType: ValueType;
    period: DatePeriod;
    hiddenItemIds: number[];
    onChangeHiddenItemIds: (
        update: (hiddenItemIds: number[]) => number[],
    ) => void;
}) => {
    const [container, setContainer] = React.useState<HTMLCanvasElement | null>(
        null,
    );
    const [chart, setChart] = React.useState<Chart<"bar"> | null>(null);
    const render = useCallback(_.debounce(RenderProductGraphByTotal, 500), []);

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
                indexAxis: "x",
                plugins: {
                    title: {
                        display: false,
                        text: "Sales",
                    },
                    tooltip: {
                        position: "nearest",
                    },
                    legend: {
                        onClick: (_evt, legendItem, legend) => {
                            const datasetId = (
                                legend.chart.data.datasets[
                                    legendItem.datasetIndex!
                                ] as any
                            ).id;
                            onChangeHiddenItemIds((prev) => {
                                if (prev.includes(datasetId)) {
                                    return prev.filter(
                                        (id) => id !== datasetId,
                                    );
                                } else {
                                    return [...prev, datasetId];
                                }
                            });
                        },
                    },
                },
                responsive: true,
                normalized: true,
                scales: {
                    x: {
                        stacked: false,
                    },
                    y: {
                        stacked: false,
                        title: {
                            display: true,
                            text: "",
                        },
                    },
                },
                animations: {
                    x: { duration: 0 },
                    y: { duration: 550, easing: "easeOutBack" },
                },
            },
        };

        const c = new Chart(container, config);
        setChart(c);

        return () => {
            c.destroy();
            render.cancel();
        };
    }, [container]);

    // Render the graph after a timeout, while loading data
    useEffect(() => {
        if (cache.isLoading) {
            render(
                chart,
                cache.cache,
                items,
                itemLabel,
                valueType,
                hiddenItemIds,
            );
        } else {
            // Render immediately if we already have the data
            render.cancel();
            RenderProductGraphByTotal(
                chart,
                cache.cache,
                items,
                itemLabel,
                valueType,
                hiddenItemIds,
            );
        }
    }, [
        chart,
        cache.cache,
        cache.version,
        cache.isLoading,
        container,
        items,
        valueType,
    ]);

    return <canvas ref={setContainer} />;
};

export const SalesChart = <
    SalesItem,
    FlattenedSalesItem extends { id: number; name: string },
>({
    initial,
    selected,
    flattenSelection,
    dataUrl,
}: {
    selected: SalesItem[];
    flattenSelection: (selected: SalesItem[]) => FlattenedSalesItem[];
    dataUrl: (
        item: FlattenedSalesItem,
        start: Date,
        end: Date,
    ) => RequestParams;
    initial?: Partial<InitialChartData> | undefined;
}) => {
    const [grouping, setGrouping] = React.useState<DateGrouping>(
        initial?.grouping ?? "week",
    );
    const [valueType, setValueType] = React.useState<ValueType>(
        initial?.valueType ?? "amount",
    );
    const { period, lastValidPeriod } = usePeriod(initial);

    const [hiddenItemIds, setHiddenItemIds] = React.useState<number[]>([]);

    const now = new Date();
    const periodTemplates = commonPeriodTemplates(now);

    const selectedProducts = useMemo(
        () => flattenSelection(selected),
        [selected],
    );

    // The API uses an exclusive end date, but it's nicer if the UI uses an inclusive range
    const exclusiveEnd = new Date(lastValidPeriod.end!);
    exclusiveEnd.setDate(exclusiveEnd.getDate() + 1);

    const cache = useDataCache<FlattenedSalesItem, SalesResponse>(
        selectedProducts,
        (lastValidPeriod.start?.getTime() ?? 0) ^
            (lastValidPeriod.end?.getTime() ?? 0),
        (p) => dataUrl(p, lastValidPeriod.start!, exclusiveEnd),
    );

    const visibleProducts = selectedProducts.filter(
        (x) => !hiddenItemIds.includes(x.id),
    );

    const totalSales = visibleProducts
        .map((x) => cache.cache(x)?.total_amount)
        .reduce(
            (a, b) => (a !== undefined && b !== undefined ? a + b : undefined),
            0,
        );
    const totalUnits = visibleProducts
        .map((x) => cache.cache(x)?.total_count)
        .reduce(
            (a, b) => (a !== undefined && b !== undefined ? a + b : undefined),
            0,
        );
    const unit =
        selectedProducts.length > 0
            ? cache.cache(selectedProducts[0]!)?.amount_unit
            : undefined;

    return (
        <>
            <div>
                <div className="uk-flex uk-flex-between uk-margin-top">
                    <ButtonGroup
                        value={grouping}
                        onChange={setGrouping}
                        options={DateGroupings}
                        label={(x) => DateGroupingNames[x]}
                    />
                    <div className="uk-flex uk-flex-middle">
                        <DatePeriodInput
                            period={period}
                            highlightChanges={false}
                            templates={periodTemplates}
                        />
                    </div>
                    <ButtonGroup
                        value={valueType}
                        onChange={setValueType}
                        options={ValueTypes}
                        label={(x) => ValueTypeNames[x]}
                    />
                </div>
                {grouping === "total" ? (
                    <ProductGraphByTotal
                        items={selectedProducts}
                        cache={cache}
                        valueType={valueType}
                        itemLabel={(id) =>
                            selectedProducts.find((p) => p.id == id)?.name ??
                            "?"
                        }
                        period={period}
                        hiddenItemIds={hiddenItemIds}
                        onChangeHiddenItemIds={setHiddenItemIds}
                    />
                ) : (
                    <ProductGraphByTime
                        items={selectedProducts}
                        grouping={grouping}
                        cache={cache}
                        valueType={valueType}
                        itemLabel={(id) =>
                            selectedProducts.find((p) => p.id == id)?.name ??
                            "?"
                        }
                        period={period}
                        hiddenItemIds={hiddenItemIds}
                        onChangeHiddenItemIds={setHiddenItemIds}
                    />
                )}
                <dl className="uk-description-list">
                    {valueType === "amount" && (
                        <>
                            <dt>Total sales during period</dt>
                            <dd>
                                {totalSales !== undefined
                                    ? totalSales.toLocaleString()
                                    : "?"}{" "}
                                {unit}
                            </dd>
                        </>
                    )}
                    {valueType === "count" && (
                        <>
                            <dt>Total units sold during period</dt>
                            <dd>
                                {totalUnits !== undefined
                                    ? totalUnits.toLocaleString()
                                    : "?"}
                            </dd>
                        </>
                    )}
                </dl>
            </div>
        </>
    );
};

type SelectItem =
    | {
          type: "single";
          product: Product;
          category_name: string;
      }
    | {
          type: "category";
          category: ProductCategory;
      };

type SelectCategories<T> = {
    type: "group";
    label: string;
    options: T[];
};

export type InitialChartData = {
    selectedProducts: (number | string)[];
    // "all" means all categories
    // Otherwise, it's a list of category ids or names
    selectedCategories: "all" | (number | string)[];
    grouping: DateGrouping;
    valueType: ValueType;
    start: Date;
    end: Date;
};

const categoryToSelectItem = (category: ProductCategory): SelectItem => ({
    type: "category",
    category: category,
});

const productToSelectItem = (
    category: ProductCategory,
    product: Product,
): SelectItem => ({
    type: "single",
    product,
    category_name: category.name,
});

export const ProductChart = ({
    categories,
    initial,
    granularity,
    allowChangingSelection = true,
}: {
    categories: ProductCategory[];
    granularity: "categories" | "products";
    initial?: Partial<InitialChartData>;
    allowChangingSelection?: boolean;
}) => {
    const groups: SelectCategories<SelectItem>[] = useMemo(() => {
        if (categories === null) return [];

        if (granularity === "categories") {
            return [
                {
                    type: "group",
                    label: "Categories",
                    options: categories.map(categoryToSelectItem),
                },
            ];
        } else {
            return categories.map((category) => ({
                type: "group" as const,
                label: category.name,
                options: [
                    categoryToSelectItem(category),
                    ...category.items.map((product) =>
                        productToSelectItem(category, product),
                    ),
                ] as SelectItem[],
            }));
        }
    }, [categories, granularity]);

    const [selected, setSelected] = React.useState<SelectItem[]>(() => {
        const result = [];
        if (initial) {
            for (const category of categories) {
                if (
                    initial.selectedCategories == "all" ||
                    (initial.selectedCategories &&
                        (initial.selectedCategories.includes(category.id) ||
                            initial.selectedCategories.includes(category.name)))
                ) {
                    result.push(categoryToSelectItem(category));
                }
                for (const product of category.items) {
                    if (
                        initial.selectedProducts &&
                        (initial.selectedProducts.includes(product.id) ||
                            initial.selectedProducts.includes(product.name))
                    ) {
                        result.push(productToSelectItem(category, product));
                    }
                }
            }
        }
        return result;
    });

    const selector = allowChangingSelection && (
        <div className="uk-form-controls">
            <Select<SelectItem, true, SelectCategories<SelectItem>>
                isSearchable={true}
                isMulti={true}
                options={groups}
                value={selected}
                formatOptionLabel={(option) => {
                    if (option.type === "single") {
                        return option.product.name;
                    } else {
                        if (granularity === "categories") {
                            return option.category.name;
                        } else {
                            return (
                                "Everything in the category " +
                                option.category.name
                            );
                        }
                    }
                }}
                formatGroupLabel={(group) => group.label}
                getOptionValue={(option) =>
                    option.type == "category"
                        ? "c" + option.category.id
                        : "" + option.product.id
                }
                filterOption={(option, rawInput) => {
                    rawInput = rawInput.toLowerCase();
                    if (option.data.type === "single") {
                        return (
                            matchesFilter(option.data.product.name, rawInput) ||
                            matchesFilter(option.data.category_name, rawInput)
                        );
                    } else {
                        return matchesFilter(
                            option.data.category.name,
                            rawInput,
                        );
                    }
                }}
                onChange={(values) => setSelected(Array.from(values))}
            />
        </div>
    );

    if (granularity === "products") {
        return (
            <>
                {selector}
                <SalesChart<SelectItem, Product>
                    selected={selected}
                    flattenSelection={flattenSelectionToProducts}
                    dataUrl={(p, start, end) => ({
                        url: `/webshop/product/${p.id}/sales`,
                        params: {
                            start: start.toISOString().substring(0, 10),
                            end: end.toISOString().substring(0, 10),
                        },
                    })}
                    initial={initial}
                />
            </>
        );
    } else {
        return (
            <>
                {selector}
                <SalesChart<SelectItem, ProductCategory>
                    selected={selected}
                    flattenSelection={(x) =>
                        x.map((x) => {
                            if (x.type === "category") {
                                return x.category;
                            } else {
                                throw new Error("Unexpected type");
                            }
                        })
                    }
                    dataUrl={(p, start, end) => ({
                        url: `/webshop/category/${p.id}/sales`,
                        params: {
                            start: start.toISOString().substring(0, 10),
                            end: end.toISOString().substring(0, 10),
                        },
                    })}
                    initial={initial}
                />
            </>
        );
    }
};
