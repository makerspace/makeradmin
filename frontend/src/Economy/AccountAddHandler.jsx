import React from 'react'

// Backbone
import AccountModel from '../Backbone/Models/Account'

import EconomyAccount from './Account'

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

module.exports = EconomyAccountAddHandler;