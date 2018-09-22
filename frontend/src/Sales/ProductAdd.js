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
        return (
            <div>
                <h2>Skapa grupp</h2>
                <ProductForm
                    product={this.product}
                    onSave={() => this.product.save().then(() => browserHistory.replace('/sales/product/' + this.product.id))}
                />
            </div>
        );
    }
}

export default GroupAdd;
