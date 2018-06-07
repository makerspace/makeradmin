import React from 'react'
import { withRouter } from 'react-router'

// Backbone
import KeyModel from '../../Models/Key'

import Keys from '../Tables/Keys'
import Key from '../Forms/Key'

module.exports = withRouter(React.createClass(
{
	getInitialState: function()
	{
		return {
			model: new KeyModel({member_id: this.props.params.member_id}),
		};
	},

	closeForm: function()
	{
		this.props.router.push("/membership/members/" + this.props.params.member_id + "/keys");
	},

	render: function()
	{
		return (
			<Key model={this.state.model} ref="edit" onCancel={this.closeForm} onCreate={this.closeForm} onRemove={this.closeForm} route={this.props.route} />
		);
	},
}));