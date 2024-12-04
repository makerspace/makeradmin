import React, { useEffect, useState } from "react";
import { useHistory, useParams } from "react-router-dom";
import Product from "../Models/Product";
import ProductForm from "../Components/ProductForm";
import { confirmModal } from "../message";

const ProductEdit = () => {
    const { id } = useParams(); // Use useParams to get the route parameter
    const [product, setProduct] = useState(null);
    const history = useHistory();

    // Fetch the product on mount
    useEffect(() => {
        const fetchedProduct = Product.getWithRelated(id);
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

    // Ensure the component has loaded the product before rendering
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
        </div>
    );
};

export default ProductEdit;
