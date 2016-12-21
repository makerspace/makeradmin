import React from 'react'

// Backbone
import AccountModel from '../..//Models/Account'

import EconomyAccount from '../../Account'

module.exports = React.createClass({
	getInitialState: function()
	{
		var account = new AccountModel({
			period: this.props.params.period,
			account_number: this.props.params.id
		});
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