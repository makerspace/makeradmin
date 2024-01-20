import { browserHistory } from "../browser_history";
import ProductForm from "../Components/ProductForm";
import { confirmModal } from "../message";
import Product from "../Models/Product";
import { withRouter } from "react-router";
import React from "react";
class ProductEdit extends React.Component {
    constructor(props) {
        super(props);
        const { id } = props.match.params;
        this.product = Product.getWithRelated(id);
    }

    render() {
        return (
            <div>
                <h2>Redigera produkt</h2>
                <ProductForm
                    product={this.product}
                    route={this.props.route}
                    onSave={() => this.product.save()}
                    onDelete={() => {
                        return confirmModal(this.product.deleteConfirmMessage())
                            .then(() => this.product.del())
                            .then(() => {
                                browserHistory.push("/sales/product/");
                            })
                            .catch(() => null);
                    }}
                />
            </div>
        );
    }
}

export default withRouter(ProductEdit);
