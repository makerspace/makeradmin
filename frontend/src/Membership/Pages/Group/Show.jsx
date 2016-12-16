import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'
import MemberCollection from '../../Collections/Member'

import Group from '../../Group'
import GroupMembers from '../../GroupMembers'

module.exports = React.createClass({
	getInitialState: function()
	{
		var group = new GroupModel({
			group_id: this.props.params.id
		});
		group.fetch();

		this.title = "Meep";
		return {
			model: group,
		};
	},

	render: function()
	{
		return (
			<div>
				<Group model={this.state.model} />
				<GroupMembers type={MemberCollection} url={"/membership/group/" + this.props.params.id + "/members"} />
			</div>
		);
	},
});
//GroupHandler.title = "Visa grupp";