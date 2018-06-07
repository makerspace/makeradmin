import React from 'react'
import Groups from '../../Tables/Groups'
import { Link } from 'react-router'

// Backbone
import MemberModel from '../../../Models/Member'

import MemberForm from '../../Forms/Member'

module.exports = React.createClass(
{
	getInitialState: function()
	{
		var member = new MemberModel({
			member_id: this.props.params.member_id
		});

		var _this = this;
		member.fetch();

		return {
			model: member,
		};
	},


	render: function()
	{
		return (
			<div>
				<MemberForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
});