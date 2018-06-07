import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'

import { Link } from 'react-router'
//import Currency from '../../../Components/Currency'

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

	renderHeader: function ()
	{
		return [
			{
				title: "#",
			},
			{
				title: "Bokföringsdatum",
			},
			{
				title: "Beskrivning",
			},
			{
				title: "Belopp",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/economy/instruction/" + row.id}>{row.verification_number}</Link></td>
				<td>{row.accounting_date}</td>
				<td>{row.title}</td>
				<td>{row.amount}</td>
				<td><Link to={"/economy/instruction/" + row.id}>Visa</Link></td>
			</tr>
		);
	},
});