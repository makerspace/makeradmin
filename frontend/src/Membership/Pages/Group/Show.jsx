import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import { Link, withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var group = new GroupModel({
			group_id: this.props.params.group_id
		});

		var _this = this;
		group.fetch({success: function()
		{
			// Since we do not use BackboneReact we have to update the view manually
			_this.forceUpdate();
		}});

		this.title = "Meep";
		return {
			model: group,
		};
	},

	render: function()
	{
		const group_id = this.props.params.group_id;
		return (
			<div>
				<h2>Grupp {this.state.model.get("title")}</h2>

				<ul className="uk-tab">
					<li><Link to={"/membership/groups/" + group_id}>Information</Link></li>
					<li><Link to={"/membership/groups/" + group_id + "/members"}>Medlemmar</Link></li>
					<li><Link to={"/membership/groups/" + group_id + "/permissions"}>Behörigheter</Link></li>
				</ul>

				{this.props.children}
			</div>
		);
	},
}));
//GroupHandler.title = "Visa grupp";