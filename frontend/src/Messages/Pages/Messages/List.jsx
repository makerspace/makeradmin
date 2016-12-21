import React from 'react'

// Backbone
import MessagesCollection from '../../Collections/Messages'

import { Link } from 'react-router'
import MessagesTable from '../../Messages'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Utskickshistorik</h2>

				<p>Visa lista över samtliga utskick.</p>

				<MessagesTable type={MessagesCollection} />
			</div>
		);
	},
});
//Messages.title = "Utskickshistorik";