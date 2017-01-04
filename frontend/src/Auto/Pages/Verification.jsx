import React from 'react'
//import config from '../../config'
import TictailRelationsTable from '../Components/Tables/TictailRelations'

// Backbone
import TictailRelationsCollection from '../Collections/TictailRelations'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h1>Skapa verifikationer</h1>

				<TictailRelationsTable type={TictailRelationsCollection} />
			</div>
		);
	},
});