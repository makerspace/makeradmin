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

	removeTextMessage: function(permission)
	{
		return "Are you sure you want to remove permission \"" + permission.permission + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Error deleting permission", {timeout: 0, status: "danger"});
	},

	removePermission: function(permission_id)
	{
		var _this = this;

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/membership/group/" + this.props.params.group_id + "/permissions/remove",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: JSON.stringify({
				permissions: [permission_id],
			}),
			contentType: "application/json; charset=utf-8",
			dataType: "json",
		}).done(function () {
			UIkit.notify("Behörighet borttagen från grupp", {status: "success"});
			_this.fetch();
		});
	},

	renderHeader: function()
	{
		return [
			{
				title: "Behörighet",
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
				<td>{row.permission}</td>
				<td>
					<TableDropdownMenu>
						<a onClick={this.removePermission.bind(this, row.permission_id)}><i className="uk-icon-trash" /> Ta bort behörighet från grupp</a>
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));