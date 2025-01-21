import React, { useEffect, useState } from "react";

import { useHistory, useParams } from "react-router-dom";

import Product from "../Models/Product";

import ProductForm from "../Components/ProductForm";

import { useJson } from "Hooks/useJson";
import { InitialChartData, ProductChart } from "Statistics/Graphs/ProductGraph";
import { ProductCategory } from "Statistics/types";
import { confirmModal } from "../message";

const ProductEdit = () => {
    const { id } = useParams<{ id?: string }>();

    const [product, setProduct] = useState<Product | null>(null);

    const history = useHistory();

    useEffect(() => {
        const fetchedProduct = Product.getWithRelated(id) as Product;

        setProduct(fetchedProduct);
    }, [id]);

    const handleSave = () => {
        if (product) {
            product.save();
        }
    };

    const handleDelete = () => {
        if (product) {
            confirmModal(product.deleteConfirmMessage())
                .then(() => product.del())

                .then(() => {
                    history.push("/sales/product/");
                })

                .catch(() => null);
        }
    };

    const { data } = useJson<ProductCategory[]>({
        url: "/webshop/product_data",
    });

    const now = new Date();
    const initial: Partial<InitialChartData> = {
        selectedCategories: [],
        selectedProducts: id !== undefined ? [parseInt(id)] : [],
        grouping: "month",
        valueType: "amount",
        start: new Date(now.getTime() - 1000 * 60 * 60 * 24 * 365),
        end: now,
    };

    if (!product) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h2>Redigera produkt</h2>

            <ProductForm
                product={product}
                onSave={handleSave}
                onDelete={handleDelete}
            />
            <h2>Sales</h2>
            {data !== null && (
                <ProductChart
                    categories={data}
                    initial={initial}
                    granularity="products"
                    allowChangingSelection={false}
                />
            )}
        </div>
    );
};

export default ProductEdit;
