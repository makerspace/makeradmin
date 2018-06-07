import React from 'react'
import OverviewTable from '../Components/Tables/Overview'

// Backbone
import OverviewCollection from '../Collections/Overview'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Tictail overview</h2>

				<a target="_blank" className="uk-button uk-button-primary" href={config.apiBasePath + "/tictail/download"}>Ladda hem ordrar från Tictail</a>

				<OverviewTable type={OverviewCollection} />
			</div>
		);
	},
});