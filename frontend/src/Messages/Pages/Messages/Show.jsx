import React from 'react'

// Backbone
import MessageModel from '../../Models/Message'
import RecipientsCollection from '../../Collections/Recipients'

//import { Link } from 'react-router'
import RecipientsTable from '../../Components/Tables/Recipients'
import Message from '../../Components/Message'

module.exports = React.createClass({
	getInitialState: function()
	{
		// Load message model
		var message = new MessageModel({
			message_id: this.props.params.id
		});
		message.fetch();

		return {
			message_model: message,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Utskick</h2>
				<Message model={this.state.message_model} />

				<RecipientsTable
					type={RecipientsCollection}
					dataSource={{
						url: "/messages/" + this.props.params.id + "/recipients",
					}}
				/>
			</div>
		);
	},
});
//Recipients.title = "";