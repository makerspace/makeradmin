import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateTimeField from '../Formatters/DateTime'

module.exports = React.createClass({
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

	renderHeader: function()
	{
		return [
			{
				title: "Skapad",
				sort: "created_at",
			},
			{
				title: "Typ",
				sort: "type",
			},
			{
				title: "Status",
				sort: "status",
			},
			{
				title: "Meddelande",
				sort: "subject",
			},
			{
				title: "Mottagare",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><DateTimeField date={row.created_at} /></td>
				<td>
					{
							row.message_type == "email" ?
								(<span><i className="uk-icon-envelope" title="E-post" /> E-post</span>)
						:
							row.message_type == "sms" ?
								(<span><i className="uk-icon-commenting" title="SMS" /> SMS</span>)
						:
							row.message_type
					}
				</td>
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
				<td><Link to={"/messages/" + row.message_id}>{row.subject}</Link></td>
				<td>{row.num_recipients}st</td>
			</tr>
		);
	},
});