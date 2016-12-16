import React from 'react'

// Backbone
import CostCenterCollection from '../../Collections/CostCenter'

import EconomyCostCenters from './../../CostCenters'

module.exports = React.createClass({
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