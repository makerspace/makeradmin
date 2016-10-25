import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../BackboneTable'
import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import TableDropdownMenu from '../TableDropdownMenu'

var TransactionsUser = React.createClass({
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
				title: "Bokföringsdatum",
				sort: "accounting_date",
			},
			{
				title: "Transaktion",
				sort: "transaction_title",
			},
			{
				title: "Belopp",
				class: "uk-text-right",
				sort: "amount",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td><DateField date={row.accounting_date}/></td>
				<td><Link to={"/economy/instruction/" + row.instruction_number}>{row.transaction_title}</Link></td>
				<td className="uk-text-right"><Currency value={row.amount} currency="SEK" /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/product/" + row.entity_id + "/edit"}><i className="uk-icon uk-icon-cog" /> Redigera metadata</Link>
						<Link to={"/economy/instruction/" + row.instruction_number}><i className="uk-icon uk-icon-cog" /> Visa verifikation</Link>
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = TransactionsUser