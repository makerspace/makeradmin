import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = React.createClass({
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
						<Link to={"/membership/groups/" + row.group_id + "/edit"}><i className="uk-icon-cog"></i> Redigera grupp</Link>
						{this.removeButton(i, "Ta bort grupp")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});