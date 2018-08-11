import React from 'react'

// Backbone
import ProductModel from '../../Models/Product'

import ProductForm from '../../Components/Forms/Product'

module.exports = React.createClass({
	getInitialState: function()
	{
		var product = new ProductModel({id: this.props.params.id});
		product.fetch();

		return {
			model: product,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera produkt</h2>
				<ProductForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
});