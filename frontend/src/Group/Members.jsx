import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../BackboneTable'
import { Link } from 'react-router'
import TableDropdownMenu from '../TableDropdownMenu'

var GroupMembers = React.createClass({
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

	removeTextMessage: function(entity)
	{
		// TODO
		return "Are you sure you want to remove group \"" + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		// TODO
		UIkit.modal.alert("Error deleting group");
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
				<td><Link to={"/members/" + row.member_number}>{row.member_number}</Link></td>
				<td><Link to={"/members/" + row.member_number}>{row.firstname} {row.lastname}</Link></td>
				<td>
					<TableDropdownMenu>
						{this.removeButton(i, "Ta bort medlem ur grupp")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = GroupMembers