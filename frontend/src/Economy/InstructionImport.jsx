import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'

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

module.exports = EconomyAccountingInstructionImport