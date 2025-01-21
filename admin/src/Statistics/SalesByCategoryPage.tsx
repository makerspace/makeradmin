import { useJson } from "Hooks/useJson";
import React from "react";
import { InitialChartData, ProductChart } from "./Graphs/ProductGraph";
import { ProductCategory } from "./types";

export default () => {
    const { data } = useJson<ProductCategory[]>({
        url: "/webshop/product_data",
    });

    const now = new Date();
    const initial: Partial<InitialChartData> = {
        selectedCategories: "all",
        selectedProducts: [],
        grouping: "month",
        valueType: "amount",
        start: new Date(now.getTime() - 1000 * 60 * 60 * 24 * 365),
        end: now,
    };

    return (
        <div className="uk-width-1-1">
            <h2>Sales by Category</h2>
            {data !== null && (
                <ProductChart
                    categories={data}
                    initial={initial}
                    granularity="categories"
                />
            )}
        </div>
    );
};
