import React from 'react'

// Backbone
import AccountingPeriodsCollection from '../../Collections/AccountingPeriods'

import EconomyAccountingPeriods from '../../AccountingPeriods'

import { Link } from 'react-router'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Räkneskapsår</h2>
				<p className="uk-float-left">På denna sida ser du en lista över samtliga räkneskapsår.</p>
				<Link to={"/settings/economy/accountingperiod/add"} className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa nytt räkneskapsår</Link>

				<EconomyAccountingPeriods type={AccountingPeriodsCollection} />
			</div>
		);
	},
});