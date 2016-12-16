import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../BackboneTable'

// Backbone
import MasterledgerCollection from '../Collections/Masterledger'

import { Link } from 'react-router'
import Currency from '../../Formatters/Currency'

var MasterLedgerHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Huvudbok</h2>
				<EconomyAccounts type={MasterledgerCollection} />
			</div>
		);
	},
});

var EconomyAccounts = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 3,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "account_number",
			},
			{
				title: "Konto",
				sort: "title",
			},
			{
				title: "Kontobalans",
				class: "uk-text-right",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/economy/account/" + row.account_number}>{row.account_number}</Link></td>
				<td>{row.title}</td>
				<td className="uk-text-right"><Currency value={row.balance} /></td>
			</tr>
		);
	},
});

module.exports = MasterLedgerHandler;