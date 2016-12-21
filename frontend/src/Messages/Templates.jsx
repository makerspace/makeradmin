import React from 'react'

import { Link, withRouter } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateTimeField from '../Formatters/DateTime'
import TableDropdownMenu from '../TableDropdownMenu'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	sendMessage: function()
	{
		// TODO: Ladda in mall
		this.props.router.push("/messages/new");
	},

	removeTextMessage: function(template)
	{
		return "Är du säker på att du vill ta bort utskicksmallen \"" + template.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Fel uppstod vid borttagning av mall");
	},

	renderHeader: function()
	{
		return [
			{
				title: "Namn",
				sort: "",
			},
			{
				title: "Rubrik",
				sort: "title",
			},
			{
				title: "Skapad",
				sort: "created_at",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		return [
			(
				<tr key={i}>
					<td>{row.name}</td>
					<td><Link to={"/messages/templates/" + row.template_id}>{row.title}</Link></td>
					<td><DateTimeField date={row.created_at} /></td>
					<td>
						<TableDropdownMenu>
							<a data-uk-toggle={"{target: \"#template-" + row.template_id + "\"}"}><i className="uk-icon-commenting"></i> Visa meddelandetext</a>
							<a onClick={this.sendMessage}><i className="uk-icon-envelope"></i> Skicka meddelande</a>
							<Link to={"/messages/templates/" + row.template_id + ""}><i className="uk-icon-cog"></i> Redigera mall</Link>
							{this.removeButton(i, "Ta bort mall")}
						</TableDropdownMenu>
					</td>
				</tr>
			),
			(
				<tr id={"template-" + row.template_id} className="uk-hidden">
					<td colSpan={5}>
						<pre>{row.description}</pre>
					</td>
				</tr>
			)
		];
	},
}));