import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 3,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	renderHeader: function ()
	{
		return [
			{
				title: "Id",
				sort: "id",
			},
			{
				title: "Namn",
				sort: "name",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/sales/category/" + row.id}>{row.id}</Link></td>
				<td><Link to={"/sales/category/" + row.id}>{row.name}</Link></td>
				<td>
					<TableDropdownMenu>
						{this.removeButton(i, "Ta bort kategori")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});