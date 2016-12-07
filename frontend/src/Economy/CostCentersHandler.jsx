import React from 'react'

// Backbone
import CostCenterCollection from '../Backbone/Collections/CostCenter'

import EconomyCostCenters from './CostCenters'

var EconomyCostCentersHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Kostnadsställen</h2>
				<EconomyCostCenters type={CostCenterCollection} />
			</div>
		);
	},
});

module.exports = EconomyCostCentersHandler;