import React from "react";

import { browserHistory } from "../browser_history";
import Product from "../Models/Product";
import ProductForm from "../Components/ProductForm";

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
