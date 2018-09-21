import React from 'react';

import {browserHistory} from 'react-router';
import Product from "../Models/Product";
import ProductForm from "../Components/ProductForm";


class GroupAdd extends React.Component {

    constructor(props) {
        super(props);
        this.product = new Product();
    }

    render() {
        
        const onSave = (actions) => {
            this.product
                .save()
                .then(() => Promise.all(actions.map(a => {a.product_id = this.product.id; return a.save();})))
                .then(() => browserHistory.replace('/sales/product/' + this.product.id));
        };
        
        return (
            <div>
                <h2>Skapa grupp</h2>
                <ProductForm
                    product={this.product}
                    onSave={onSave}
                />
            </div>
        );
    }
}

export default GroupAdd;
