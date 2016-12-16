import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import Currency from '../Formatters/Currency'
//import DateField from '../Formatters/Date'
import TableDropdownMenu from '../TableDropdownMenu'


module.exports = React.createClass({
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