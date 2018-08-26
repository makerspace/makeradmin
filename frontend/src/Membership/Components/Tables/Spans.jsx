import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import DateField from '../../../Components/Date'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 8,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(span)
	{
		return "Are you sure you want to remove membership span \"" + span.span_id + " from member #" + span.member_number + ": " + span.firstname + " " + span.lastname + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Ett fel uppstod vid borttagning av medlemsperiod", {timeout: 0, status: "danger"});
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "span_id",
			},
			{
				title: "Typ",
				sort: "type",
			},
			{
				title: "#",
				sort: "member_id",
			},
			{
				title: "Förnamn",
				sort: "firstname",
			},
			{
				title: "Efternamn",
				sort: "lastname",
			},
			{
				title: "Start",
				sort: "startdate",
			},
			{
				title: "Slut",
				sort: "enddate",
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
				<td><Link to={"/membership/spans/" + row.span_id}>{row.span_id}</Link></td>
				<td><Link to={"/membership/spans/" + row.span_id}>{row.span_type}</Link></td>
				<td>{row.member_number}</td>
				<td>{row.firstname}</td>
				<td>{row.lastname}</td>
				<td><DateField date={row.startdate} /></td>
				<td><DateField date={row.enddate} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/membership/spans/" + row.span_id}><i className="uk-icon-cog"></i> Visa period</Link>
						{this.removeButton(i, "Ta bort medlemsperiod")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});