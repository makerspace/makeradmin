import React from 'react'
import MessagesTable from '../Tables/RecipientsUser'

// Backbone
import RecipientsCollection from '../../Collections/Recipients'

import { Link } from 'react-router'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<MessagesTable
					type={RecipientsCollection}
					dataSource={{
						url: "/messages/user/" + this.props.params.member_id,
					}}
				/>
				<Link to={"/membership/members/" + this.props.params.member_id + "/messages/new"} className="uk-button uk-button-primary"><i className="uk-icon-envelope" /> Skicka meddelande</Link>
			</div>
		);
	},
});