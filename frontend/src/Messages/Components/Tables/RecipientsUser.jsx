import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import DateTimeField from '../../../Components/DateTime'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
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
				title: "Status",
				sort: "status",
			},
			{
				title: "Mottagare",
				sort: "recipient",
			},
			{
				title: "Meddelande",
				sort: "subject",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		// Trim the subject to a better length
		if(row.subject.length > 33)
		{
			row.subject = row.subject.substr(0, 30) + "...";
		}

		return [
			(
				<tr key={i}>
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
					<td>
						{
								row.message_type == "email" ?
									(<span><i className="uk-icon-envelope" title="E-post" /> {row.recipient}</span>)
							:
								row.message_type == "sms" ?
									(<span><i className="uk-icon-commenting" title="SMS" /> {row.recipient}</span>)
							:
								row.message_type
						}
					</td>
					<td>{row.subject}</td>
					<td className="uk-text-right">
						<a data-uk-toggle={"{target: \"#recipient-" + row.recipient_id + "\"}"}>Visa meddelande <i className="uk-icon-angle-down" /></a>
					</td>
				</tr>
			),
			(
				<tr id={"recipient-" + row.recipient_id} className="uk-hidden">
					<td colSpan={4}>
						{row.message_type != "sms" ? <h3>{row.subject}</h3> : ''}
						<p>{row.body}</p>
					</td>
				</tr>
			)
		];
	},
});