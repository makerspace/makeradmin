import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import Group from '../../Group'

module.exports = React.createClass({
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
				<Group model={this.state.model} />
			</div>
		);
	},
});