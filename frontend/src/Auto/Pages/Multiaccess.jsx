import React from 'react'
import MultiaccessTable from '../Components/Tables/Multiaccess'

// Backbone
import MultiaccessCollection from '../Collections/Multiaccess'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h1>Multiaccess differans</h1>

				<MultiaccessTable type={MultiaccessCollection} />
			</div>
		);
	},
});