import React from 'react'
import BackboneReact from 'backbone-react-component'

//import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
//import DateField from '../Formatters/Date'

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
		this.state.collection.fetch();
	},

	renderHeader: function ()
	{
		return [
			{
				title: "Member",
			},
			{
				title: "Startdatum",
			},
			{
				title: "Beskrivning",
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
				<td>{row.date_start}</td>
				<td>{row.title}</td>
				<td>{row.product_id}</td>
			</tr>
		);
	},
});