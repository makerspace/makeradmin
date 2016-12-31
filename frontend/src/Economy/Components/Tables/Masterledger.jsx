import React from 'react'
import BackboneTable from '../../../BackboneTable'
import { Link, withRouter } from 'react-router'
import Currency from '../../../Components/Currency'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 3,
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
				sort: "account_number",
			},
			{
				title: "Konto",
				sort: "title",
			},
			{
				title: "Kontobalans",
				class: "uk-text-right",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/economy/" + this.props.params.period + "/account/" + row.account_number}>{row.account_number}</Link></td>
				<td>{row.title}</td>
				<td className="uk-text-right"><Currency value={row.balance} /></td>
			</tr>
		);
	},
}));