import { browserHistory } from "../browser_history";
import ProductForm from "../Components/ProductForm";
import Product from "../Models/Product";
import React from "react";
class ProductAdd extends React.Component {
    constructor(props) {
        super(props);
        this.product = new Product();
    }

    render() {
        return (
            <div>
                <h2>Skapa produkt</h2>
                <ProductForm
                    product={this.product}
                    onSave={() =>
                        this.product
                            .save()
                            .then(() =>
                                browserHistory.replace(
                                    "/sales/product/" + this.product.id,
                                ),
                            )
                    }
                />
            </div>
        );
    }
}

export default ProductAdd;
