import React from 'react'

import { Link, withRouter } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import DateTimeField from '../../../Components/DateTime'
import TableDropdownMenu from '../../../TableDropdownMenu'
import classNames from 'classnames/bind'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
			showRow: {},
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(template)
	{
		return "Är du säker på att du vill ta bort utskicksmallen \"" + template.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Fel uppstod vid borttagning av mall", {timeout: 0, status: "danger"});
	},

	renderHeader: function()
	{
		return [
			{
				title: "Namn",
				sort: "name",
			},
			{
				title: "Rubrik",
				sort: "title",
			},
			{
				title: "",
			},
		];
	},

	toggle: function(template_id)
	{
		this.state.showRow[template_id] = !this.state.showRow[template_id];
		this.forceUpdate();
	},

	renderRow: function(row, i)
	{
		var classes = classNames({
			"toggle": true,
			"show": this.state.showRow.hasOwnProperty(row.template_id) && this.state.showRow[row.template_id],
		});

		return [
			(
				<tr key={i}>
					<td>{row.name}</td>
					<td><Link to={"/messages/templates/" + row.template_id}>{row.title}</Link></td>
					<td className="uk-text-right">
						<a className="uk-margin-small-right uk-button uk-button-mini uk-button-success" onClick={this.toggle.bind(this, row.template_id)}>
							{this.state.showRow.hasOwnProperty(row.template_id) && this.state.showRow[row.template_id] == true ? 
								<div><i className="uk-icon-angle-up"></i> Dölj</div>
							:
								<div><i className="uk-icon-angle-down"></i> Visa</div>
							}
						</a>
						<Link className="uk-margin-small-right uk-button uk-button-mini uk-button-primary" to={"/messages/new?template=" + row.template_id} ><i className="uk-icon-envelope"></i> Skicka</Link>
						<TableDropdownMenu>
							<Link to={"/messages/templates/" + row.template_id + ""}><i className="uk-icon-cog"></i> Redigera mall</Link>
							{this.removeButton(i, "Ta bort mall")}
						</TableDropdownMenu>
					</td>
				</tr>
			),
			(
				<tr className={classes}>
					<td colSpan={5}>
						<div className="wrapper">
							<div className="scrolling">
								{row.description.split("\n").map(function(item) {
									return (
										<span>
											{item}
											<br/>
										</span>
									)
								})}
							</div>
						</div>
					</td>
				</tr>
			)
		];
	},
}));