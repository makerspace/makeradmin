import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import Currency from '../../../Components/Currency'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
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
				sort: "name",
			},
			{
				title: "Kategori",
				sort: "category_id",
			},
			{
				title: "Pris",
				sort: "price",
			},
			{
				title: "Enhet",
				sort: "unit",
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
				<td><Link to={"/sales/product/" + row.id}>{row.name}</Link></td>
				<td>{row.category_id}</td>
 				<td className="uk-text-right"><Currency value={row.smallest_multiple*100*row.price} />kr</td>
				<td>{row.smallest_multiple == 1 ? row.unit : row.smallest_multiple + " " + row.unit}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/sales/product/" + row.id}><i className="uk-icon-cog" /> Redigera produkt</Link>
						{this.removeButton(i, "Ta bort produkt")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});