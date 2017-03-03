import React from 'react'

import { Link, withRouter } from 'react-router'
import Currency from '../../../Components/Currency'
import GenericEntityFunctions from '../../../GenericEntityFunctions'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	render: function()
	{
		if(this.state.model.transactions.length == 0)
		{
			var content = <tr><td colSpan="4"><em>Denna verifikation saknar bokförda poster</em></td></tr>;
		}
		else
		{
			var _this = this;
			var content = this.state.model.transactions.map(function (row, i)
			{
				return (
					<tr key={i}>
						<td>
							<Link to={"/economy/" + _this.state.model.period + "/account/" + row.account_number}>{row.account_number} {row.account_title}</Link>
						</td>
						<td>{row.title}</td>
						<td className="uk-text-right"><Currency value={row.balance} /></td>
					</tr>
				);
			})
		}

		if(this.state.model.entity_id == 0)
		{
			var title = "Skapa verifikation";
		}
		else
		{
			var title = this.state.model.instruction_number === null ? "Preliminär verifikation" : "Verifikation " + this.state.model.instruction_number;
			title = title + " - " + this.state.model.title;
		}

		if(this.state.model.files.length == 0)
		{
			var files = <tr><td colSpan="4"><em>Det finns inga filer kopplade till denna verifikation</em></td></tr>;
		}
		else
		{
			var _this = this;
			var files = this.state.model.files.map(function (file, i)
			{
				return (
					<tr key={i}>
						<td><a href={"/economy/" + _this.props.params.period + "/file/" + _this.state.model.external_id + "/" + file}>{file}</a></td>
					</tr>
				);
			})
		}

		return (
			<div>
				<h2>{title}</h2>

				<form className="uk-form uk-form-horizontal">
					<div className="uk-grid">
						<div className="uk-width-1-6">
							<label className="uk-form-label">Verifikationsnr</label>
						</div>
						<div className="uk-width-2-6">
							<div className="uk-form-icon">
								<i className="uk-icon-tag"></i>
								<input type="text" value={this.state.model.instruction_number} disabled />
							</div>
						</div>
						<div className="uk-width-1-6">
							<label className="uk-form-label">Skapad</label>
						</div>
						<div className="uk-width-2-6">
							<div className="uk-form-icon">
								<i className="uk-icon-calendar"></i>
								<input type="text" value={this.state.model.created_at} disabled />
							</div>
						</div>
					</div>
					<div className="uk-grid">
						<div className="uk-width-1-6">
							<label className="uk-form-label">Bokföringsdatum</label>
						</div>
						<div className="uk-width-2-6">
							<div className="uk-form-icon">
								<i className="uk-icon-calendar"></i>
								<input type="text" value={this.state.model.accounting_date} onChange={this.handleChange} />
							</div>
						</div>
						<div className="uk-width-1-6">
							<label className="uk-form-label">Ändrad</label>
						</div>
						<div className="uk-width-2-6">
							<div className="uk-form-icon">
								<i className="uk-icon-calendar"></i>
								<input type="text" value={this.state.model.updated_at} disabled />
							</div>
						</div>
					</div>

					<div className="uk-grid">
						<div className="uk-width-1-6">
							<label className="uk-form-label">Belopp</label>
						</div>
						<div className="uk-width-2-6">
							<div className="uk-form-icon">
								<i className="uk-icon-usd"></i>
								<input type="text" value={this.state.model.balance} disabled />
							</div>
						</div>
						{ this.state.model.entity_id != 0 ?
							<div className="uk-width-1-6">
								<label className="uk-form-label">Importerad från</label>
							</div>
						: "" }
						{ this.state.model.entity_id != 0 ?
							<div className="uk-width-2-6">
								<div className="uk-form-icon">
									<i className="uk-icon-institution"></i>
									<input type="text" value={this.state.model.importer} disabled />
								</div>
								<p><em><Link to={"/economy/" + this.props.params.period + "/instruction/" + this.state.model.instruction_number + "/import"}>Visa data från import</Link></em></p>
							</div>
						: "" }
					</div>

					<div className="uk-grid">
						<div className="uk-width-1-6">
							<label className="uk-form-label">Kommentar</label>
						</div>
						<div className="uk-width-3-6">
							<textarea value={this.state.model.description} onChange={this.handleChange} />
						</div>
					</div>
				</form>

				<table className="uk-table">
					<thead>
						<tr>
							<th>Konto</th>
							<th>Kommentar</th>
							<th className="uk-text-right">Belopp</th>
						</tr>
					</thead>
					<tbody>
						{content}
					</tbody>
				</table>

				<table className="uk-table">
					<thead>
						<tr>
							<th>Filnamn</th>
						</tr>
					</thead>
					<tbody>
						{files}
					</tbody>
				</table>
			</div>
		);
	},
}));