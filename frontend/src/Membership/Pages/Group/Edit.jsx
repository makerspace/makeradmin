import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import Group from '../../Group'

module.exports = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;
		var group = new GroupModel({group_id: id});
		group.fetch();

		this.title = "Meep";
		return {
			model: group,
		};
	},

	render: function()
	{
		return (
			<Group model={this.state.model} />
		);
	},
});
//GroupEditHandler.title = "Visa grupp";