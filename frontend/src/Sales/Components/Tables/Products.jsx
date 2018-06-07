import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import Currency from '../../../Components/Currency'
//import DateField from '../../../Components/Date'
import TableDropdownMenu from '../../../TableDropdownMenu'


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
		this.fetch();
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove product \"" + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Error deleting product", {timeout: 0, status: "danger"});
	},

	renderHeader: function()
	{
		return [
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
				<td><Link to={"/sales/product/" + row.product_id}>{row.title}</Link></td>
				<td>{row.expiry_date}</td>
				<td>{row.auto_extend}</td>
				<td>{row.interval}</td>
				<td><Currency value={row.price} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/sales/product/" + row.product_id}><i className="uk-icon-cog" /> Redigera produkt</Link>
						{this.removeButton(i, "Ta bort produkt")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});