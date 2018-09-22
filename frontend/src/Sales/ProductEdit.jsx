import React from 'react';
import {withRouter} from "react-router";
import Product from "../Models/Product";
import ProductForm from "../Components/ProductForm";
import {confirmModal} from "../message";


class ProductEdit extends React.Component {
    
    constructor(props) {
        super(props);
        const {id} = props.params;
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
                            .then(() => this.product.del(), () => false)
                            .then(() => {
                                this.props.router.push("/sales/product/");
                            });
                    }}
                />
            </div>
        );
    }
}

export default withRouter(ProductEdit);
