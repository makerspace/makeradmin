import React from 'react'
import { MailHistory } from '../Mail/History'

// Backbone
import MailCollection from '../Backbone/Collections/Mail'

import { Link } from 'react-router'

var MailUserBox = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<MailHistory type={MailCollection}
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
				<Link to="/mail/send" className="uk-button uk-button-primary"><i className="uk-icon-envelope" /> Skicka meddelande</Link>
			</div>
		);
	},
});

module.exports = MailUserBox