import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import CostCenterModel from '../Backbone/Models/CostCenter'
import CostCenterCollection from '../Backbone/Collections/CostCenter'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import BackboneTable from '../BackboneTable'

var EconomyCostCentersHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Kostnadsställen</h2>
				<EconomyCostCenters type={CostCenterCollection} />
			</div>
		);
	},
});

var EconomyCostCenterHandler = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;

		var costcenter = new CostCenterModel({id: id});
		costcenter.fetch();

		return {
			model: costcenter
		};
	},

	render: function()
	{
		return (<EconomyCostCenter model={this.state.model} />);
	}
});

var EconomyCostCenters = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	renderHeader: function ()
	{
		return [
			{
				title: "#",
			},
			{
				title: "Bokföringsdatum",
			},
			{
				title: "Beskrivning",
			},
			{
				title: "Belopp",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/economy/instruction/" + row.id}>{row.verification_number}</Link></td>
				<td>{row.accounting_date}</td>
				<td>{row.title}</td>
				<td>{row.amount}</td>
				<td><Link to={"/economy/instruction/" + row.id}>Visa</Link></td>
			</tr>
		);
	},
});

module.exports = {
	EconomyCostCentersHandler,
	EconomyCostCenterHandler,
}