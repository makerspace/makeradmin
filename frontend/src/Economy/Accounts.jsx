import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../BackboneTable'

import { Link } from 'react-router'
import TableDropdownMenu from '../TableDropdownMenu'

var EconomyAccounts = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},


	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove account \"" + entity.account_number + " " + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting account");
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "account_number",
			},
			{
				title: "Konto",
				sort: "title",
			},
			{
				title: "Beskrivning",
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
				<td><Link to={"/settings/economy/account/" + row.account_number + "/edit"}>{row.account_number}</Link></td>
				<td>{row.title}</td>
				<td>{row.description}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/settings/economy/account/" + row.account_number + "/edit"}><i className="uk-icon-cog"></i> Redigera konto</Link>
						{this.removeButton(i, "Ta bort konto")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = EconomyAccounts;