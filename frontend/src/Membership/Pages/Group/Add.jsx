import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import Group from '../../Components/Forms/Group'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var newGroup = new GroupModel();
		return {
			model: newGroup,
		};
	},

	render: function()
	{
		return (
			<div>
				<Group model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));