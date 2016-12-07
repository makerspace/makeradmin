import React from 'react'

// Backbone
import AccountModel from '../Backbone/Models/Account'

import EconomyAccount from './Account'

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

module.exports = EconomyAccountEditHandler;