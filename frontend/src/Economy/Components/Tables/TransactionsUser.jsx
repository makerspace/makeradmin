import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'
import { Link } from 'react-router'
import Currency from '../../../Components/Currency'
import DateField from '../../../Components/Date'
import TableDropdownMenu from '../../../TableDropdownMenu'

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
				<td><Link to={"/economy/" + row.period + "/instruction/" + row.instruction_number}>{row.transaction_title}</Link></td>
				<td className="uk-text-right"><Currency value={row.amount} currency="SEK" /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/product/" + row.entity_id + "/edit"}><i className="uk-icon-cog" /> Redigera metadata</Link>
						<Link to={"/economy/" + row.period + "/instruction/" + row.instruction_number}><i className="uk-icon-cog" /> Visa verifikation</Link>
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});