import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'
import { Link, withRouter } from 'react-router'
import TableDropdownMenu from '../../../TableDropdownMenu'
import auth from '../../../auth'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 3,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(group)
	{
		return "Are you sure you want to remove group \"" + group.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Error deleting group", {timeout: 0, status: "danger"});
	},

	removeUser: function(member_id)
	{
		var _this = this;

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/membership/member/" + member_id + "/groups/remove",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: JSON.stringify({
				groups: [this.props.params.group_id],
			}),
			contentType: "application/json; charset=utf-8",
			dataType: "json",
		}).done(function () {
			UIkit.notify("Medlem borttagen ur grupp", {status: "success"});
			_this.fetch();
		});
	},

	renderHeader: function()
	{
		return [
			{
				title: "Medlemsnummer",
			},
			{
				title: "Namn",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/membership/members/" + row.member_id}>{row.member_number}</Link></td>
				<td><Link to={"/membership/members/" + row.member_id}>{row.firstname} {row.lastname}</Link></td>
				<td>
					<TableDropdownMenu>
						<a onClick={this.removeUser.bind(this, row.member_id)}><i className="uk-icon-trash" /> Ta bort medlem ur grupp</a>
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));