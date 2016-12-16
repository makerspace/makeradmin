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
				title: "Medlem",
				sort: "recipient_id",
			},
			{
				title: "Rubrik",
				sort: "title",
			},
			{
				title: "Meddelande",
				sort: "description",
			},
			{
				title: "Mottagare",
				sort: "recipient",
			},
			{
				title: "Status",
				sort: "status",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/member/" + row.member_id}>{row.member_id}</Link></td>
				<td>{row.title}</td>
				<td>{row.description}</td>
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
			</tr>
		);
	},
});