import React from 'react'

// Backbone
import GroupModel from '../../../Models/Group'

import GroupForm from '../../Forms/Group'

module.exports = React.createClass(
{
	getInitialState: function()
	{
		var group = new GroupModel({
			group_id: this.props.params.group_id
		});

		var _this = this;
		group.fetch();

		return {
			model: group,
		};
	},


	render: function()
	{
		return (
			<div>
				<GroupForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
});