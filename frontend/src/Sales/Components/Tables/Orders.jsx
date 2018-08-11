import React from 'react'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import Currency from '../../../Components/Currency'

module.exports = React.createClass({
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

	renderHeader: function ()
	{
		return [
			{
				title: "Order",
				sort: "id",
			},
			{
				title: "Datum",
				sort: "created_at",
			},
			{
				title: "Payment",
				sort: "status",
			},
			{
				title: "Medlem",
				sort: "member_id",
			},
			{
				title: "Belopp",
				class: "uk-text-right",
				sort: "amount",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/sales/order/" + row.id}>{row.id}</Link></td>
				<td>{row.created_at}</td>
				<td>{row.status}</td>
				<td><Link to={"/membership/members/" + row.member_id}>{row.member_number}: {row.member_name}</Link></td>
				<td className="uk-text-right"><Currency value={100 * row.amount} /> kr</td>
			</tr>
		);
	},
});
