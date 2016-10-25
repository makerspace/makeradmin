import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import InvoiceCollection from '../Backbone/Collections/Invoice'
import InvoiceModel from '../Backbone/Models/Invoice'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import BackboneTable from '../BackboneTable'
import TableFilterBox from '../TableFilterBox'

var InvoiceListHandler = React.createClass({
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
			<div className="uk-width-1-1">
				<h2>Fakturor</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga fakturor för det valda bokföringsåret.</p>
				<Link to={"/economy/invoice/add"} className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny faktura</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<InvoiceList type={InvoiceCollection} filters={this.state.filters} />
			</div>
		);
	},
});
InvoiceListHandler.title = "Visa fakturor";

var InvoiceHandler = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;
		var invoice = new InvoiceModel({id: id});
		invoice.fetch();

		return {
			model: invoice
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Faktura</h2>
				<Invoice model={this.state.model} />
			</div>
		);
	},
});

var InvoiceAddHandler = React.createClass({
	getInitialState: function()
	{
		var invoice = new InvoiceModel();

		return {
			model: invoice
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa faktura</h2>
				<Invoice model={this.state.model} />
			</div>
		);
	},
});

var InvoiceList = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 6,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
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

var Invoice = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	render: function()
	{
		if(this.state.model.posts.length == 0)
		{
			var content = <tr><td colSpan="4"><em>Denna faktura saknar innehåll</em></td></tr>;
		}
		else
		{
			var currency = this.state.model.currency;
			var content = this.state.model.posts.map(function (row, i)
			{
				// row.weight
				// row.type

				if(row.vat === null)
				{
					row.vat = "0%";
				}

				return (
					<tr key={i}>
						<td>{row.title}</td>
						<td className="uk-text-right"><Currency value={row.price} currency={currency} /></td>
						<td className="uk-text-right">{row.amount} {row.unit}</td>
						<td className="uk-text-right"><Currency value={row._total} currency={currency} /></td>
						<td className="uk-text-right">{row.vat}</td>
					</tr>
				);
			})
		}

		return (
			<div className="invoice">
				<a href={"/api/v2/economy/2015/invoice/" + this.state.model.invoice_number + "/export"}>Exportera *.ODT</a>

				<div className="uk-grid">
					<div className="uk-width-1-3 box">
						<div className="title">Mottagare</div>
						<div className="data">{this.state.model.title}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Belopp</div>
						<div className="data"><Currency value={this.state.model._total} currency={currency} /></div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Status</div>
						<div className="data">{this.state.model.status}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Er referens</div>
						<div className="data">{this.state.model.your_reference}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Fakturadatum</div>
						<div className="data">{this.state.model.date_invoice}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Fakturanummer</div>
						<div className="data">{this.state.model.invoice_number}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Vår referens</div>
						<div className="data">{this.state.model.our_reference}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Förfallodatum</div>
						<div className="data">{this.state.model.date_expiry}</div>
					</div>

					<div className="uk-width-1-3 box">
						<div className="title">Betalningsvillkor</div>
						<div className="data">{this.state.model.conditions} dagar</div>
					</div>
				</div>

				<div className="box">
					<div className="title">Kommentar</div>
					<div className="data">
						<pre>{this.state.model.description}</pre>
					</div>
				</div>

				<div className="box">
					<div className="title">Adress</div>
					<div className="data">
						<pre>{this.state.model.address}</pre>
					</div>
				</div>

				<table className="uk-table uk-table-striped">
					<thead>
						<tr>
							<th>Titel</th>
							<th className="uk-text-right">Pris</th>
							<th className="uk-text-right">Antal</th>
							<th className="uk-text-right">Totalt</th>
							<th className="uk-text-right">MOMS</th>
						</tr>
					</thead>
					<tbody>
						{content}
					</tbody>
				</table>
			</div>
		);
	},
});

module.exports = {
	InvoiceListHandler,
	InvoiceHandler,
	InvoiceAddHandler,
}