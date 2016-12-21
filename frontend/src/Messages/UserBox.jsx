import React from 'react'
import MessagesTable from './Recipients'

// Backbone
import RecipientsCollection from './Collections/Recipients'

import { Link } from 'react-router'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<MessagesTable type={RecipientsCollection} params={{member_id: this.props.member_id}} />
				<Link to="/messages/new" className="uk-button uk-button-primary"><i className="uk-icon-envelope" /> Skicka meddelande</Link>
			</div>
		);
	},
});