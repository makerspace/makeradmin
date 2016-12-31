import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import Group from '../../Components/Forms/Group'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		console.log(this.props.params);
		var group = new GroupModel({group_id: this.props.params.group_id});
		group.fetch();

		return {
			model: group,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera grupp</h2>
				<Group model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));
//GroupEditHandler.title = "Visa grupp";