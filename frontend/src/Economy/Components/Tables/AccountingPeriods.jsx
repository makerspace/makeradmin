import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'

import config from '../../../config'

import DateField from '../../../Components/Date'
import { Link, withRouter } from 'react-router'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
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
				title: "Period",
				sort: "start",
			},
			{
				title: "",
			},
		];
	},

	activatePeriod: function(period)
	{
/*
		console.log("Aktivera räkneskapsår " + period);

		// TODO: Set config
		console.log("Gammalt val: " + config.accountingPeriod);
		config.accountingPeriod = period;
*/

		this.props.router.push("/economy/" + period);
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/settings/economy/accountingperiod/" + row.accountingperiod_id + "/edit"}>{row.name}</Link></td>
				<td>{row.title}</td>
				<td><DateField date={row.start} /> - <DateField date={row.end} /></td>
				<td>
					<TableDropdownMenu>
						<a onClick={this.activatePeriod.bind(this, row.name)}><i className="uk-icon-check"></i> Välj räkneskaper</a>
						<Link to={"/settings/economy/accountingperiod/" + row.accountingperiod_id + "/edit"}><i className="uk-icon-cog"></i> Redigera räkneskapsår</Link>
						{this.removeButton(i, "Ta bort räkneskapsår")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));