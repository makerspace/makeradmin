import React from 'react'
import { Link, withRouter } from 'react-router'

// Backbone
import MemberModel from '../../Models/Member'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var member = new MemberModel({
			member_id: this.props.params.member_id
		});

		var _this = this;
		member.fetch({success: function()
		{
			// Since we do not use BackboneReact we have to update the view manually
			_this.forceUpdate();
		}});

		return {
			model: member,
		};
	},

	render: function()
	{
		var member_id = this.props.params.member_id;
		return (
			<div>
				<h2>Medlem #{this.state.model.get("member_number")}: {this.state.model.get("firstname")} {this.state.model.get("lastname")}</h2>

				<ul className="uk-tab">
					<li><Link to={"/membership/members/" + member_id}>Personuppgifter</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/groups"}>Grupper</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/keys"}>Nycklar</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/permissions"}>Behörigheter</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/transactions"}>Transaktioner</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/messages"}>Utskick</Link></li>
				</ul>

				{this.props.children}
			</div>
		);
	},
}));
//MemberHandler.title = "Visa medlem";