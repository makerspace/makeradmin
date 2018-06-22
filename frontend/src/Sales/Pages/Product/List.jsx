import React from 'react'

// Backbone
import ProductCollection from '../../Collections/Product'
import Products from '../../Components/Tables/Products'
import { Link } from 'react-router'
import TableFilterBox from '../../../TableFilterBox'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			filters: {},
		};
	},

	overrideFiltersFromProps: function(filters)
	{
		return filters;
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	render: function()
	{
		return (
			<div>
				<h2>Produkter</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
				<Link className="uk-button uk-button-primary uk-float-right" to="/sales/product/add"><i className="uk-icon-plus-circle"></i> Skapa ny produkt</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<Products type={ProductCollection} filters={this.state.filters} />
			</div>
		);
	},
});