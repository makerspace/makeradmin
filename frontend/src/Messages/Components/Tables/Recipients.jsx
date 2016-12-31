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
				title: "Medlem",
				sort: "recipient_id",
			},
			{
				title: "Mottagare",
				sort: "recipient",
			},
			{
				title: "Status",
				sort: "status",
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
					<td><Link to={"/membership/members/" + row.member_id + "/messages"}>Visa</Link></td>
					<td>{row.recipient}</td>
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