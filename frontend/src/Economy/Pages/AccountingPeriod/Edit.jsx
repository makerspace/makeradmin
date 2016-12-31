import React from 'react'

// Backbone
import AccountingPeriodModel from '../../Models/AccountingPeriod'

import EconomyAccountingPeriod from '../../Components/Forms/AccountingPeriod'

module.exports = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;

		var accountingperiod = new AccountingPeriodModel({accountingperiod_id: id});
		accountingperiod.fetch();

		return {
			model: accountingperiod,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera räkneskapsår</h2>
				<EconomyAccountingPeriod model={this.state.model} />
			</div>
		);
	},
});