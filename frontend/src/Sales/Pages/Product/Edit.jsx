import React from 'react'

// Backbone
import ProductModel from '../../Models/Product'

import ProductForm from '../../Components/Forms/Product'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Redigera produkt</h2>

				<ProductForm />
			</div>
		);
	},
});