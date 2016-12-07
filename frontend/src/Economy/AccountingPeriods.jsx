import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../BackboneTable'

import DateTime from '../Formatters/DateTime'
import { Link } from 'react-router'
import TableDropdownMenu from '../TableDropdownMenu'

var AccountingPeriods = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove period \"" + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting period");
	},

	renderHeader: function()
	{
		return [
			{
				title: "Namn",
				sort: "name",
			},
			{
				title: "Titel",
				sort: "title",
			},
			{
				title: "Beskrivning",
				sort: "description",
			},
			{
				title: "Startdatum",
				sort: "start",
			},
			{
				title: "Slutdatum",
				sort: "end",
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
				<td><Link to={"/settings/economy/accountingperiod/" + row.accountingperiod_id + "/edit"}>{row.name}</Link></td>
				<td>{row.title}</td>
				<td>{row.description}</td>
				<td><DateTime date={row.start} /></td>
				<td><DateTime date={row.end} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/settings/economy/accountingperiod/" + row.accountingperiod_id + "/edit"}><i className="uk-icon uk-icon-cog"></i> Redigera konto</Link>
						{this.removeButton(i, "Ta bort konto")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = AccountingPeriods;