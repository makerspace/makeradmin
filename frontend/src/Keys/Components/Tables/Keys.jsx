import React from 'react'
import BackboneTable from '../../../BackboneTable'
import TableDropdownMenu from '../../../TableDropdownMenu'
import { Link, withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
			linkPrefix: this.props.linkPrefix ? this.props.linkPrefix : "",
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove key \"" + entity.tagid + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting key");
	},

	onEdit: function(key)
	{
		this.props.router.push(this.state.linkPrefix + "/keys/" + key.get("key_id"));
	},

	renderHeader: function()
	{
		return [
			{
				title: "RFID",
				sort: "tagid",
			},
			{
				title: "Medlem",
				sort: "member_id",
			},
			{
				title: "Kommentarer",
				sort: "description",
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
				<td><Link to={this.state.linkPrefix + "/keys/" + row.key_id}>{row.tagid}</Link></td>
				<td><Link to={"/membership/members/" + row.member_id}>{row.member_number}</Link></td>
				<td><Link to={this.state.linkPrefix + "/keys/" + row.key_id}>{row.description}</Link></td>
				<td>
					<TableDropdownMenu>
						{this.editButton(i)}
						{this.removeButton(i)}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));