import React from 'react'
import Groups from '../../Tables/MemberGroups'
import { Link } from 'react-router'

// Backbone
import GroupCollection from '../../../Collections/Group'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<Groups type={GroupCollection} dataSource={{
					url: "/membership/member/" + this.props.params.member_id + "/groups"
				}} />
				<Link to={"/membership/members/" + this.props.params.member_id + "/groups/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle" /> Lägg till grupp</Link>
			</div>
		);
	},
});