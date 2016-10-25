import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import MasterledgerCollection from '../Backbone/Collections/Masterledger'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import Currency from '../Formatters/Currency'

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

var EconomyOverviewHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Översikt</h2>
				<ul>
					<li>Samtliga obetalda fakturor + 3 senaste betalda</li>
					<li>5 senaste skapade/ändrade verifikationerna</li>
					<li>Saldo på konton (Bank, Stripe, PayPal, etc)</li>
					<li>Datum för senaste synkroniseringar (Bank, Stripe, PayPal, etc)</li>
				</ul>
			</div>
		);
	},
});

var EconomyDebugHandler = React.createClass({
	render: function ()
	{

		return (
			<div className="uk-width-1-1">
				<h2>Debug</h2>
			</div>
		);
	}
});

var EconomyAccountingPeriodHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Räkneskapsår</h2>
				<p>Konfiguera räkneskapsår</p>
			</div>
		);
	},
});

module.exports = {
	EconomyOverviewHandler,
	MasterLedgerHandler,
	EconomyDebugHandler,
	EconomyAccountingPeriodHandler,
}