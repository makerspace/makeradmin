import React from "react";

import { useNavigate } from "react-router-dom";

import Product from "../Models/Product";

import ProductForm from "../Components/ProductForm";

const ProductAdd = () => {
    const product = new Product();

    const navigate = useNavigate();

    const handleSave = () => {
        product.save().then(() => {
            navigate(`/sales/product/${product.id}`, { replace: true });
        });
    };

    return (
        <div>
            <h2>Skapa produkt</h2>

            <ProductForm product={product} onSave={handleSave} />
        </div>
    );
};

export default ProductAdd;
