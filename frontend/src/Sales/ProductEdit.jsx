import React from 'react';
import {withRouter} from "react-router";
import Product from "../Models/Product";
import ProductForm from "../Components/ProductForm";
import {confirmModal} from "../message";
import {get} from "../gateway";
import ProductAction from "../Models/ProductAction";


class ProductEdit extends React.Component {
    
    constructor(props) {
        super(props);
        const {id} = props.params;
        this.product = Product.get(id);
        this.state = {actions: []};
        get({url: "/webshop/product_action", params: {product_id: this.props.params.id}})
            .then((data) => this.setState({actions: data.data.map(d => new ProductAction(d))}));
    }
    
    render() {
        const onSave = (actions) => {
            this.product.save()
                .then(() => Promise.all(this.state.actions.map(a => a.del())))
                .then(() => Promise.all(actions.map(a => {a.product_id = this.product.id; return a.save();})))
                .then(() => this.setState({actions}));
        };
        
        return (
            <div>
                <h2>Redigera produkt</h2>
                <ProductForm
                    actions={this.state.actions}
                    product={this.product}
                    route={this.props.route}
                    onSave={onSave}
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
