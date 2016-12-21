import React from 'react'
import { withRouter } from 'react-router'
import MessageForm from '../../Components/Forms/Message'

// Backbone
import MessageModel from '../../Models/Message'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		return {
			model: new MessageModel(),
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa utskick</h2>
				<MessageForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));
//MailSendHandler.title = "Skapa utskick";