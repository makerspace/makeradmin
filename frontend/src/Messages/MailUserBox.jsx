import React from 'react'
import { MessagesTable } from './Messages'

// Backbone
import MessagesCollection from './Collections/Messages'

import { Link } from 'react-router'

module.exports = React.createClass(
{
	render: function()
	{
		return (<span>TODO: Mail</span>);

		return (
			<div>
				<MessagesTable type={MessagesCollection}
					filters={{
						relations:
						[
							{
								type: "member",
								member_number: this.props.member_number,
							}
						]
					}}
				/>
				<Link to="/messages/new" className="uk-button uk-button-primary"><i className="uk-icon-envelope" /> Skicka meddelande</Link>
			</div>
		);
	},
});