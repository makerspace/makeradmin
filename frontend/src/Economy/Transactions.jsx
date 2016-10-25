import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../BackboneTable'
import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'

var Transactions = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 6,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	renderHeader: function()
	{
		return [
			{
				title: "Bokföringsdatum",
			},
			{
				title: "Verifikation",
			},
			{
				title: "Transaktion",
			},
			{
				title: "Belopp",
				class: "uk-text-right",
			},
			{
				title: "Saldo",
				class: "uk-text-right",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function (row, i)
	{
		if(typeof row.files != "undefined")
		{
			var icon = <i className="uk-icon-file"></i>;
		}
		else
		{
			var icon = "";
		}

		return (
			<tr key={i}>
				<td><DateField date={row.accounting_date}/></td>
				<td><Link to={"/economy/instruction/" + row.instruction_number}>{row.instruction_number} {row.instruction_title}</Link></td>
				<td>{row.transaction_title}</td>
				<td className="uk-text-right"><Currency value={row.amount} currency="SEK" /></td>
				<td className="uk-text-right"><Currency value={row.balance} currency="SEK" /></td>
				<td>{icon}</td>
			</tr>
		);
	},
});

module.exports = Transactions