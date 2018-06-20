import React from 'react'
import GroupMembers from '../../Tables/GroupMembers'
import { Link } from 'react-router'

// Backbone
import MemberCollection from '../../../Collections/Member'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<GroupMembers type={MemberCollection} dataSource={{
					url: "/membership/group/" + this.props.params.group_id + "/members"
				}} />
				<Link to={"/membership/groups/" + this.props.params.group_id + "/members/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle" /> Lägg till medlem</Link>
			</div>
		);
	},
});