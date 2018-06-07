import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'

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
				title: "#",
				sort: "invoice_number",
			},
			{
				title: "Förfallodatum",
				sort: "date_expiry",
			},
			{
				title: "Mottagare",
				sort: "title",
			},
			{
				title: "Referens",
				sort: "your_reference",
			},
			{
				title: "Belopp",
				class: "uk-text-right",
				sort: "_total",
			},
			{
				title: "Status",
				sort: "status",
			},
		];
	},

	renderRow: function(row, i)
	{
		if(row.status == "unpaid")
		{
			row.status = "Obetald";
		}

		return (
			<tr key={i}>
				<td><Link to={"/economy/invoice/" + row.invoice_number}>{row.invoice_number}</Link></td>
				<td><DateField date={row.date_expiry} /></td>
				<td>{row.title}</td>
				<td>{row.your_reference}</td>
				<td className="uk-text-right"><Currency value={row._total} currency={row.currency} /></td>
				<td>{row.status}</td>
			</tr>
		);
	},
});