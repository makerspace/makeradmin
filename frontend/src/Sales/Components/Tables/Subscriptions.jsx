import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import DateField from '../../../Components/Date'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
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
				title: "Medlem",
			},
			{
				title: "Startdatum",
				sort: "date_start",
			},
			{
				title: "Beskrivning",
				sort: "description",
			},
			{
				title: "Produkt",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td>{row.member_id}</td>
				<td><DateField date={row.date_start} /></td>
				<td>{row.title}</td>
				<td><Link to={"/sales/product/" + row.product_id}>Visa</Link></td>
			</tr>
		);
	},
});