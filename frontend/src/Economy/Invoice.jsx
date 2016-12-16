import React from 'react'
import BackboneReact from 'backbone-react-component'

import config from '../config'

// Backbone
import InvoiceCollection from './Collections/Invoice'
import InvoiceModel from './Models/Invoice'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import BackboneTable from '../BackboneTable'
import TableFilterBox from '../TableFilterBox'

module.exports = React.createClass({
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
				<a href={"/economy/" + config.accountingPeriod + "/invoice/" + this.state.model.invoice_number + "/export"}>Exportera *.ODT</a>

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