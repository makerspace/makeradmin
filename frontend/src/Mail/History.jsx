import React from 'react'

// Backbone
import MailModel from '../Backbone/Models/Mail'
import MailCollection from '../Backbone/Collections/Mail'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateTimeField from '../Formatters/DateTime'

var MailHistoryHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Historik</h2>

				<p className="uk-float-left">Visa lista över samtliga E-post och SMS-utskick.</p>
				<Link to="/mail/send" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa nytt utskick</Link>

				<MailHistory type={MailCollection} />
			</div>
		);
	},
});
MailHistoryHandler.title = "Utskickshistorik";

var MailHistory = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 6,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	componentWillReceiveProps: function(nextProps)
	{
		if(nextProps.filters != this.state.filters)
		{
			this.setState({
				filters: nextProps.filters
			});

			// TODO: setState() has a delay so we need to wait a moment
			var _this = this;
			setTimeout(function() {
				_this.fetch();
			}, 100);
		}
	},

	renderHeader: function()
	{
		return [
			{
				title: "Id",
				sort: "entity_id",
			},
			{
				title: "Status",
				sort: "status",
			},
			{
				title: "Mottagare",
				sort: "recipient",
			},
			{
				title: "Meddelande",
				sort: "description",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/mail/" + row.entity_id}>{row.entity_id}</Link></td>
				<td>
					{(() => {
						switch (row.status) {
							case "queued": return <span>Köad <DateTimeField date={row.created_at} /></span>;
							case "failed": return "Sändning misslyckades";
							case "sent":   return <span>Skickad <DateTimeField date={row.date_sent} /></span>;
							default:       return "Okänt";
						}
					})()}
				</td>
				<td>{ row.type == "email" ? <i className="uk-icon-envelope" title="E-mail"></i> : <i className="uk-icon-commenting" title="SMS"></i> } {row.recipient}</td>
				<td>{ row.type == "email" ? row.title : row.description }</td>
			</tr>
		);
	},
});

module.exports = {
	MailHistoryHandler,
	MailHistory
}