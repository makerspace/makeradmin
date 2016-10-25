import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import SalesHistoryCollection from '../Backbone/Collections/SalesHistory'
import SalesHistoryModel from '../Backbone/Models/SalesHistory'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateField from '../Formatters/Date'
import Currency from '../Formatters/Currency'

import TableFilterBox from '../TableFilterBox'

var SalesHistoryHandler = React.createClass({
	getInitialState: function()
	{
		return {
			filters: this.props.filters || {},
		};
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	overrideFiltersFromProps: function(filters)
	{
		return filters;
	},

	render: function()
	{
		return (
			<div>
				<h2>Försäljningshistorik</h2>
				<p>På denna sida ser du en lista på samtliga sålda produkter.</p>
				<TableFilterBox onChange={this.updateFilters} />
				<History type={SalesHistoryCollection} filters={this.state.filters} />
			</div>
		);
	},
});
SalesHistoryHandler.title = "Visa försäljning";

var History = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

	renderHeader: function ()
	{
		return [
			{
				title: "Datum",
				sort: "accounting_date",
			},
			{
				title: "Order",
				sort: "extid",
			},
			{
				title: "Medlem",
				sort: "member_number",
			},
			{
				title: "Beskrivning",
			},
			{
				title: "Produkt",
				sort: "product_title",
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
				<td>{row.accounting_date}</td>
				<td><Link to={"/entity/" + row.entity_id}>{row.extid}</Link></td>
				<td><Link to={"/members/" + row.member_number}>{row.member_firstname} {row.member_lastname}</Link></td>
				<td>{row.instruction_title}</td>
				<td><Link to={"/sales/products/" + row.product_id}>{row.product_title}</Link></td>
				<td className="uk-text-right"><Currency value={-1 * row.amount} /></td>
			</tr>
		);
	},
});

module.exports = {
	SalesHistoryHandler
}