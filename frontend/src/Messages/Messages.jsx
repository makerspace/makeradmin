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
				sort: "description",
			},
			{
				title: "Antal mottagare",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><DateTimeField date={row.created_at} /></td>
				<td>
					{ row.type == "email" ?
							<span><i className="uk-icon-envelope" title="E-mail"></i> E-post</span>
						:
							<span><i className="uk-icon-commenting" title="SMS"></i> SMS</span>
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
				<td>{ row.type == "email" ? row.title : row.description }</td>
				<td>{row.num_recipients} <Link to={"/messages/" + row.message_id + "/recipients"}>Visa</Link></td>
			</tr>
		);
	},
});