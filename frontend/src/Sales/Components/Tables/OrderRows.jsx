import React from 'react'

import BackboneTable from '../../../BackboneTable'
import { Link, withRouter } from 'react-router'
import Currency from '../../../Components/Currency'

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

	renderHeader: function()
	{
		return [
			{
				title: "Rad",
				class: "uk-text-right",
			},
			{
				title: "Produkt",
			},
			{
				title: "Pris",
				class: "uk-text-right",
			},
			{
				title: "Antal",
			},
			{
				title: "Summa",
				class: "uk-text-right",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td className="uk-text-right">{i+1}</td>
				<td><Link to={"/sales/product/" + row.product_id}>{row.product_name}</Link></td>
				<td className="uk-text-right"><Currency value={100 * row.amount / row.count} /> kr</td>
				<td>{row.count}</td>
				<td className="uk-text-right"><Currency value={100 * row.amount} /> kr</td>
			</tr>
		);
	},
}));