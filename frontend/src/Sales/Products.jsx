import React from 'react'

// Backbone
import ProductCollection from '../Backbone/Collections/Product'
import ProductModel from '../Backbone/Models/Product'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import TableDropdownMenu from '../TableDropdownMenu'

var SalesProductsHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Produkter</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
				<Link to="/product/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny produkt</Link>

				<Products type={ProductCollection}/>
			</div>
		);
	},
});

var Products = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove product \"" + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting product");
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "entity_id",
			},
			{
				title: "Namn",
				sort: "title",
			},
			{
				title: "Giltig till",
				sort: "expiry_date",
			},
			{
				title: "Prenumeration",
				sort: "auto_extend",
			},
			{
				title: "Giltighetstid",
				sort: "interval",
			},
			{
				title: "Pris",
				sort: "price",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td>{row.entity_id}</td>
				<td><Link to={"/product/" + row.entity_id}>{row.title}</Link></td>
				<td>{row.expiry_date}</td>
				<td>{row.auto_extend}</td>
				<td>{row.interval}</td>
				<td><Currency value={row.price} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/product/" + row.entity_id + "/edit"}><i className="uk-icon uk-icon-cog" /> Redigera produkt</Link>
						{this.removeButton(i, "Ta bort produkt")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = {
	SalesProductsHandler,
	Products,
}