import React from 'react'
import MessagesTable from '../Tables/Recipients'

// Backbone
import MessageModel from '../../Models/Message'

import { Link, withRouter } from 'react-router'
import MessageForm from '../../Components/Forms/Message'

module.exports = withRouter(React.createClass(
{
	getInitialState: function()
	{
		var newModel = new MessageModel();

		return {
			model: newModel,
		};
	},

	onCancel: function()
	{
		// Reset the recipients field so the page exit handler don't whine
		this.state.model.set("recipients", []);

		// Go back to members messages
		this.props.router.push("/membership/members/" + this.props.params.member_id + "/messages");
	},

	onCreate: function(model)
	{
		this.setState({ignoreExitHook: true});
		this.props.router.push("/membership/members/" + this.props.params.member_id + "/messages");
		UIkit.notify("Ditt meddelande har skickats", {status: "success"});
	},

	render: function()
	{
		return (
			<div>
				<MessageForm recipient={{type: "member", id: this.props.params.member_id}} ref="message" model={this.state.model} onCancel={this.onCancel} onCreate={this.onCreate} route={this.props.route} />
			</div>
		);
	},
}));