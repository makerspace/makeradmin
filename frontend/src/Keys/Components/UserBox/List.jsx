import React from 'react'
import { Link, withRouter } from 'react-router'

// Backbone
import KeysCollection from '../../Collections/Keys'

import Keys from '../Tables/Keys'
import Key from '../Forms/Key'

module.exports = withRouter(React.createClass(
{
	onEdit: function(key)
	{
		this.props.router.push("/membership/members/" + this.props.params.member_id + "/keys/" + key.get("key_id"));
	},

	render: function()
	{
		return (
			<div>
				<Keys
					type={KeysCollection}
					dataSource={{
						url: "/membership/member/" + this.props.params.member_id + "/keys"
					}}
					onEdit={this.onEdit}
					route={this.props.route}
				/>
				<Link to={"/membership/members/" + this.props.params.member_id + "/keys/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle" /> Lägg till ny RFID-tagg</Link>
			</div>
		);
	},
}));