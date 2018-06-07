import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../../BackboneTable'

import { Link, withRouter } from 'react-router'
import Currency from '../../../Components/Currency'
import DateField from '../../../Components/Date'
import TableDropdownMenu from '../../../TableDropdownMenu'

module.exports = withRouter(React.createClass({
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
				sort: "instruction_number",
			},
			{
				title: "Bokföringsdatum",
				sort: "accounting_date",
			},
			{
				title: "Beskrivning",
				sort: "title",
			},
			{
				title: "Belopp",
				class: "uk-text-right",
			},
			{
				title: "",
			},
			{
				title: "",
			},
		];
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove instruction \"" + entity.instruction_number + " " + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting instruction");
	},

	renderRow: function (row, i)
	{
//		if(typeof row.files != "undefined")
		if(row.has_vouchers)
		{
			var icon = <i className="uk-icon-file"></i>;
		}
		else
		{
			var icon = "";
		}

		return (
			<tr key={i}>
				<td><Link to={"/economy/" + this.props.params.period + "/instruction/" + row.instruction_number}>{row.instruction_number}</Link></td>
				<td><DateField date={row.accounting_date}/></td>
				<td>{row.title}</td>
				<td className="uk-text-right"><Currency value={row.balance}/></td>
				<td>{icon}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/economy/" + this.props.params.period + "/instruction/" + row.instruction_number}><i className="uk-icon-cog"/> Redigera verifikation</Link>
						{this.removeButton(i, "Ta bort verifikation")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
}));