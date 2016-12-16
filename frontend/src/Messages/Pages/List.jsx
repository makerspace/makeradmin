import React from 'react'

// Backbone
import MessagesCollection from '../Collections/Messages'

import { Link } from 'react-router'
import MessagesTable from '../Messages'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Utskickshistorik</h2>

				<p className="uk-float-left">Visa lista över samtliga utskick.</p>
				<Link to="/messages/new" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa nytt utskick</Link>

				<MessagesTable type={MessagesCollection} />
			</div>
		);
	},
});
//Messages.title = "Utskickshistorik";