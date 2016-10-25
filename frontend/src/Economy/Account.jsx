import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import AccountModel from '../Backbone/Models/Account'
import AccountCollection from '../Backbone/Collections/Account'
import TransactionCollection from '../Backbone/Collections/Transaction'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import BackboneTable from '../BackboneTable'

import { EconomyAccountingInstructionList } from './Instruction'
import Transactions from './Transactions'
import TableDropdownMenu from '../TableDropdownMenu'

var EconomyAccountsHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Konton</h2>

				<p className="uk-float-left">På denna sida ser du en lista över samtliga bokföringskonton, även de som inte har några bokförda verifikationer.</p>
				<Link to={"/economy/account/add"} className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa nytt konto</Link>

				<EconomyAccounts type={AccountCollection} />
			</div>
		);
	},
});

var EconomyAccountHandler = React.createClass({
	getInitialState: function()
	{
		// Load account model
		var account = new AccountModel({
			account_number: this.props.params.id
		});
		account.fetch();

		return {
			account_model: account,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Konto</h2>
				<EconomyAccount model={this.state.account_model} />
				<Transactions type={TransactionCollection} filters={
					{
						account_number: this.state.account_model.get("account_number")
					}
				}/>
			</div>
		);
	},
});

var EconomyAccountEditHandler = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;

		var account = new AccountModel({account_number: id});
		account.fetch();

		return {
			model: account,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera konto</h2>
				<EconomyAccount model={this.state.model} />
			</div>
		);
	},
});

var EconomyAccountAddHandler = React.createClass({
	getInitialState: function()
	{
		var account = new AccountModel();

		return {
			model: account,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa konto</h2>
				<EconomyAccount model={this.state.model} />
			</div>
		);
	},
});

var EconomyAccounts = React.createClass({
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


	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove account \"" + entity.account_number + " " + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting account");
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
				title: "Beskrivning",
				sort: "description",
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
				<td><Link to={"/settings/economy/account/" + row.account_number + "/edit"}>{row.account_number}</Link></td>
				<td>{row.title}</td>
				<td>{row.description}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/settings/economy/account/" + row.account_number + "/edit"}><i className="uk-icon uk-icon-cog"></i> Redigera konto</Link>
						{this.removeButton(i, "Ta bort konto")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

var EconomyAccount = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.state.model[key] = target.value;

		// When we change the value of the model we have to rerender the component
		this.forceUpdate();
	},

	render: function()
	{
		return (
			<div>
				<form className="uk-form uk-form-horizontal">
					<div className="uk-form-row">
						<label className="uk-form-label">Kontonummer</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-database"></i>
								<input type="text" value={this.state.model.account_number} className="uk-form-width-large" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Titel</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-database"></i>
								<input type="text" value={this.state.model.title} className="uk-form-width-large" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Beskrivning</label>
						<div className="uk-form-controls">
							<textarea value={this.state.model.description} className="uk-form-width-large" onChange={this.handleChange} />
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Balans</label>
						<div className="uk-form-controls">
							<Currency value={this.state.model.balance} />
						</div>
					</div>
				</form>
			</div>
		);
	},
});

module.exports = {
	EconomyAccountsHandler,
	EconomyAccountHandler,
	EconomyAccountEditHandler,
	EconomyAccountAddHandler,
}