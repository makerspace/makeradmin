import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import InstructionCollection from '../Backbone/Collections/Instruction'
import InstructionModel from '../Backbone/Models/Instruction'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import BackboneTable from '../BackboneTable'
import TableDropdownMenu from '../TableDropdownMenu'
import TableFilterBox from '../TableFilterBox'

var EconomyAccountingInstructionsHandler = React.createClass({
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
				<h2>Verifikationer</h2>

				<p className="uk-float-left">Lista över samtliga verifikationer i bokföringen</p>
				<Link to="/economy/instruction/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny verifikation</Link>

				<TableFilterBox onChange={this.updateFilters} />

				<EconomyAccountingInstructionList type={InstructionCollection} filters={this.state.filters} />
			</div>
		);
	}
});
EconomyAccountingInstructionsHandler.title = "Visa verifikationer";

var EconomyAccountingInstructionHandler = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel({instruction_number: this.props.params.id});
		instruction.fetch();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return (<EconomyAccountingInstruction model={this.state.model} />);
	}
});

var EconomyAccountingInstructionAddHandler = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return (<EconomyAccountingInstruction model={this.state.model} />);
	}
});

var EconomyAccountingInstructionImportHandler = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel({instruction_number: this.props.params.id});
		instruction.fetch();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return <EconomyAccountingInstructionImport model={this.state.model} />
	}
});

var EconomyAccountingInstructionList = React.createClass({
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
				<td><Link to={"/economy/instruction/" + row.instruction_number}>{row.instruction_number}</Link></td>
				<td><DateField date={row.accounting_date}/></td>
				<td>{row.title}</td>
				<td className="uk-text-right"><Currency value={row.balance}/></td>
				<td>{icon}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/economy/instruction/" + row.instruction_number}><i className="uk-icon uk-icon-cog"/> Redigera verifikation</Link>
						{this.removeButton(i, "Ta bort verifikation")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

var EconomyAccountingInstruction = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.state.model[key] = target.value;

		// When we change the value of the model we have to rerender the component
		this.forceUpdate();
	},

	render: function()
	{
		if(this.state.model.transactions.length == 0)
		{
			var content = <tr><td colSpan="4"><em>Denna verifikation saknar bokförda poster</em></td></tr>;
		}
		else
		{
			var content = this.state.model.transactions.map(function (row, i)
			{
				return (
					<tr key={i}>
						<td>
							<Link to={"/economy/account/" + row.account_number}>{row.account_number} {row.account_title}</Link>
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
			var title = this.state.model.instruction_number === null ? 'Preliminär verifikation' : 'Verifikation ' + this.state.model.instruction_number;
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
						<td><a href={"/api/v2/economy/2015/file/" + _this.state.model.external_id + "/" + file}>{file}</a></td>
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
								<p><em><Link to={"/economy/instruction/" + this.state.model.id + "/import"}>Visa data från import</Link></em></p>
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
});

var EconomyAccountingInstructionImport = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	render: function()
	{
		return (
				<div>
					<h3>Data från import</h3>
					<Link to={"/economy/instruction/" + this.state.model.id}>Tillbaka till verifikation</Link>
					<form className="uk-form uk-form-horizontal">
					<div className="uk-grid">
						<div className="uk-width-1-2">
							<div className="uk-form-row">
								<label className="uk-form-label">Importerad från</label>
								<div className="uk-form-controls">
									<div className="uk-form-icon">
										<i className="uk-icon-institution"></i>
										<input type="text" value={this.state.model.importer} disabled />
									</div>
								</div>
							</div>

							<div className="uk-form-row">
								<label className="uk-form-label">Externt id</label>
								<div className="uk-form-controls">
									<div className="uk-form-icon">
										<i className="uk-icon-database"></i>
										<input type="text" value={this.state.model.external_id} disabled />
									</div>
								</div>
							</div>

							<div className="uk-form-row">
								<label className="uk-form-label">Externt datum</label>
								<div className="uk-form-controls">
									<div className="uk-form-icon">
										<i className="uk-icon-database"></i>
										<input type="text" value={this.state.model.external_date} disabled />
									</div>
								</div>
							</div>

							<div className="uk-form-row">
								<label className="uk-form-label">Data</label>
								<div className="uk-form-controls">
									<textarea value={this.state.model.external_data} />
								</div>
							</div>
						</div>
					</div>
					</form>
				</div>
		);
	},
});

module.exports = {
	EconomyAccountingInstructionsHandler,
	EconomyAccountingInstructionAddHandler,
	EconomyAccountingInstructionHandler,
	EconomyAccountingInstructionImportHandler,
	EconomyAccountingInstructionList,
}