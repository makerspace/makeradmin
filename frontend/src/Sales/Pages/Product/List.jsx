import React from 'react'

// Backbone
import ProductCollection from '../../Collections/Product'

import Products from '../../Components/Tables/Products'
import { Link } from 'react-router'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Produkter</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
				<Link to="/sales/product/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny produkt</Link>

				<Products type={ProductCollection} />
			</div>
		);
	},
});