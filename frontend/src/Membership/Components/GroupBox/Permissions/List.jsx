import React from 'react'
import Permissions from '../../Tables/GroupPermissions'
import { Link } from 'react-router'

// Backbone
import PermissionCollection from '../../../Collections/Permission'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<Permissions type={PermissionCollection} dataSource={{
					url: "/membership/group/" + this.props.params.group_id + "/permissions"
				}} />
				<Link to={"/membership/groups/" + this.props.params.group_id + "/permissions/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle" /> Lägg till behörighet</Link>
			</div>
		);
	},
});