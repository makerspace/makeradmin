import React from 'react'
import Permissions from '../../Tables/MemberPermissions'

// Backbone
import PermissionCollection from '../../../Collections/Permission'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<Permissions type={PermissionCollection} dataSource={{
					url: "/membership/member/" + this.props.params.member_id + "/permissions"
				}} />
			</div>
		);
	},
});