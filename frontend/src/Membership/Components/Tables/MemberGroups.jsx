import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'
import { Link, withRouter } from 'react-router'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 9,
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

	removeUser: function(group_id)
	{
		var _this = this;

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/membership/member/" + this.props.params.member_id + "/groups/remove",
			data: JSON.stringify({
				groups: [group_id],
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
				title: "Titel",
				sort: "title",
			},
			{
				title: "Antal medlemmar",
				sort: "membercount",
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
				<td><Link to={"/membership/groups/" + row.group_id}>{row.title}</Link></td>
				<td>{row.num_members}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/membership/groups/" + row.group_id + "/edit"}><i className="uk-icon-cog" /> Redigera grupp</Link>
						<a onClick={this.removeUser.bind(this, row.group_id)}><i className="uk-icon-trash" /> Ta bort medlem ur grupp</a>
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));