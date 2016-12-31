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
		// Fetch the model from server
		var newModel = new KeyModel({key_id: this.props.params.key_id})
		newModel.fetch();

		return {
			model: newModel,
		};
	},

	closeForm: function()
	{
		this.props.router.push("/membership/members/" + this.props.params.member_id + "/keys");
	},

	render: function()
	{
		return (
			<Key model={this.state.model} ref="edit" member_number={this.props.member_number} onCancel={this.closeForm} onUpdate={this.closeForm} onRemove={this.closeForm} route={this.props.route} />
		);
	},
}));