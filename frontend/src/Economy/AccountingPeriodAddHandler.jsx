import React from 'react'

// Backbone
import AccountingPeriodModel from '../Backbone/Models/Account'

import EconomyAccountingPeriod from './AccountingPeriod'

var AccountingPeriodAddHandler = React.createClass({
	getInitialState: function()
	{
		var account = new AccountingPeriodModel();

		return {
			model: account,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa räkneskapsår</h2>
				<EconomyAccountingPeriod model={this.state.model} />
			</div>
		);
	},
});

module.exports = AccountingPeriodAddHandler;